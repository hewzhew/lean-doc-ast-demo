# parser_new/syntax_parser.py
# 状态：当前版本 - 正在使用的新版语法解析器

import re
from typing import List, Dict, Any
# 从同级目录的 tokenizer.py 中导入 Token 和 TokenType
from .tokenizer import Token, TokenType

class SyntaxParser:
    """
    语法分析器：接收词元列表，构建并返回一个代表文档结构的 AST。
    当前版本 - 替代了旧版本的解析器模块
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        """安全地获取当前词元，如果到达末尾则返回 EOF 词元。"""
        if self.is_at_end():
            return self.tokens[-1]
        return self.tokens[self.pos]

    def advance(self):
        """向前移动一个位置。"""
        if not self.is_at_end():
            self.pos += 1

    def is_at_end(self) -> bool:
        """检查是否已处理完所有词元。"""
        # -1 是因为我们有一个 EOF 词元在最后
        return self.pos >= len(self.tokens) - 1

    def parse(self) -> List[Dict[str, Any]]:
        """主解析函数：返回 AST 节点列表。"""
        ast = []
        
        while not self.is_at_end():
            # 跳过所有换行
            while not self.is_at_end() and self.current_token().type == TokenType.NEWLINE:
                self.advance()
            
            if self.is_at_end():
                break
            
            node = self.parse_block()
            if node:
                ast.append(node)
            else:
                self.advance()
        
        return ast

    def parse_block(self) -> Dict[str, Any]:
        """块级路由：根据当前词元类型，决定调用哪个具体的块解析函数。"""
        token = self.current_token()
        
        if token.type in [TokenType.CONTAINER_END, TokenType.BLOCK_END_THREE_COLON, TokenType.EOF]:
            return None

        if token.type == TokenType.BLOCK_START_THREE_COLON:
            if re.search(r'\bshow\s*:=', token.value):
                content = self.current_token().value
                self.advance()
                return {
                    "type": "DefinitionBlock",
                    "content": content.strip(),
                    "translatable": False
                }
            else:
                return self.parse_simple_block()

        route = {
            TokenType.CONTAINER_START: self.parse_container_block,
            TokenType.PERCENT_FENCE: self.parse_metadata_block,
            TokenType.HEADER: self.parse_header,
            TokenType.CODE_FENCE: self.parse_code_block,
            TokenType.DOC_COMMENT_START: self.parse_doc_comment,
            TokenType.DOC_DIRECTIVE: self.parse_doc_directive,
            TokenType.CODE_KEYWORD: self.parse_code_keyword,
            TokenType.DEF_TERM: self.parse_definition_list,  # 新增定义列表路由
            # 新增特殊指令路由
            TokenType.INCLUDE_DIRECTIVE: self.parse_include_directive,
            TokenType.DOCSTRING_PLACEHOLDER: self.parse_docstring_placeholder,
            # 新增内联角色路由（虽然它们通常在段落中处理）
            TokenType.LEAN_ROLE: self.parse_inline_role,
            TokenType.NAME_ROLE: self.parse_inline_role,
            TokenType.KEYWORD_ROLE: self.parse_inline_role,
            TokenType.TACTIC_ROLE: self.parse_inline_role,
            TokenType.OPTION_ROLE: self.parse_inline_role,
            TokenType.TODO_ROLE: self.parse_inline_role,
            TokenType.TECH_ROLE: self.parse_inline_role,
            TokenType.REF_ROLE: self.parse_inline_role,
        }
        
        parse_func = route.get(token.type, self.parse_paragraph)
        return parse_func()

    # 新增：解析定义列表
    def parse_definition_list(self) -> Dict[str, Any]:
        """
        解析定义列表：
        : term_name
          描述内容
        """
        definitions = []
        
        while not self.is_at_end() and self.current_token().type == TokenType.DEF_TERM:
            # 解析术语
            term_content = self.current_token().value.strip()[1:].strip()  # 去掉开头的 ':'
            self.advance()
            
            # 跳过换行
            while not self.is_at_end() and self.current_token().type == TokenType.NEWLINE:
                self.advance()
            
            # 收集描述内容（缩进的段落）
            description_parts = []
            while not self.is_at_end():
                token = self.current_token()
                
                # 检查是否到达下一个术语或块级元素
                if (token.type == TokenType.DEF_TERM or
                    token.type in [TokenType.HEADER, TokenType.CODE_FENCE, 
                                  TokenType.CONTAINER_START, TokenType.CONTAINER_END,
                                  TokenType.BLOCK_START_THREE_COLON, TokenType.BLOCK_END_THREE_COLON,
                                  TokenType.PERCENT_FENCE, TokenType.EOF]):
                    break
                
                # 检查双换行（定义结束）
                if (token.type == TokenType.NEWLINE and 
                    self.pos + 1 < len(self.tokens) and 
                    self.tokens[self.pos + 1].type == TokenType.NEWLINE):
                    break
                
                description_parts.append(token.value)
                self.advance()
            
            # 解析描述内容中的内联角色
            description_text = "".join(description_parts).strip()
            description_content = self._parse_inline_content(description_text)
            
            definitions.append({
                "term": term_content,
                "description": description_content
            })
        
        return {
            "type": "DefinitionList",
            "definitions": definitions,
            "translatable": True
        }
    
    def _parse_inline_content(self, text: str) -> List[Dict[str, Any]]:
        """
        解析文本中的内联角色，返回内容节点列表
        """
        if not text:
            return []
        
        # 创建临时的 tokenizer 来处理内联内容
        from .tokenizer import Tokenizer
        temp_tokenizer = Tokenizer()
        tokens = temp_tokenizer.tokenize(text)
        
        content = []
        current_text = ""
        
        for token in tokens:
            if token.type == TokenType.EOF:
                break
                
            inline_role_types = [
                TokenType.LEAN_ROLE, TokenType.NAME_ROLE, TokenType.KEYWORD_ROLE,
                TokenType.TACTIC_ROLE, TokenType.OPTION_ROLE, TokenType.TODO_ROLE,
                TokenType.TECH_ROLE, TokenType.REF_ROLE,
                TokenType.INCLUDE_DIRECTIVE, TokenType.DOCSTRING_PLACEHOLDER
            ]
            
            if token.type in inline_role_types:
                # 先保存累积的文本
                if current_text:
                    content.append({"type": "Text", "content": current_text})
                    current_text = ""
                # 添加内联角色
                content.append({
                    "type": "InlineRole",
                    "role_type": token.type.name,
                    "content": token.value,
                    "translatable": False
                })
            else:
                current_text += token.value
        
        # 处理剩余文本
        if current_text:
            content.append({"type": "Text", "content": current_text})
        
        return content

    def parse_inline_role(self) -> Dict[str, Any]:
        """解析内联角色标记。"""
        content = self.current_token().value
        role_type = self.current_token().type.name
        self.advance()
        return {
            "type": "InlineRole",
            "role_type": role_type,
            "content": content,
            "translatable": False
        }

    def parse_include_directive(self) -> Dict[str, Any]:
        """解析 {include ...} 指令。"""
        content = self.current_token().value
        self.advance()
        return {
            "type": "IncludeDirective",
            "content": content,
            "translatable": False
        }

    def parse_docstring_placeholder(self) -> Dict[str, Any]:
        """解析 {docstring ...} 占位符。"""
        content = self.current_token().value
        self.advance()
        return {
            "type": "DocstringPlaceholder",
            "content": content,
            "translatable": False
        }

    def parse_header(self) -> Dict[str, Any]:
        level = len(self.current_token().value)
        self.advance()
        content = ""
        while not self.is_at_end() and self.current_token().type != TokenType.NEWLINE:
            content += self.current_token().value
            self.advance()
        return {"type": "Header", "level": level, "content": {"original": content.strip(), "translated": ""}}

    def parse_code_block(self) -> Dict[str, Any]:
        """解析代码块，提取语言标识符和参数。"""
        start_line = self.current_token().value
        language = ""
        params = {}
        
        if start_line.startswith("```"):
            lang_part = start_line[3:].strip()
            param_match = re.search(r'^(\w+)\s*\(([^)]+)\)', lang_part)
            if param_match:
                language = param_match.group(1)
                param_str = param_match.group(2)
                for param in param_str.split(','):
                    param = param.strip()
                    if ':=' in param:
                        key, value = param.split(':=', 1)
                        key = key.strip()
                        value = value.strip().strip('"')
                        params[key] = value
            else:
                language = lang_part
        
        self.advance()
        
        content_lines = []
        while not self.is_at_end() and not (self.current_token().type == TokenType.CODE_FENCE and self.current_token().value.startswith("```")):
            content_lines.append(self.current_token().value)
            self.advance()
        
        if not self.is_at_end() and self.current_token().type == TokenType.CODE_FENCE:
            self.advance()
        
        return {
            "type": "CodeBlock",
            "language": language,
            "params": params,
            "content": "".join(content_lines).strip(),
            "translatable": False
        }

    def parse_paragraph(self) -> Dict[str, Any]:
        """解析段落，内容现在是子节点列表，保留单个换行符。"""
        children = []
        current_text = ""
        
        def flush_text():
            """将累积的文本添加为Text节点"""
            nonlocal current_text
            if current_text:
                children.append({"type": "Text", "content": current_text})
                current_text = ""
        
        while not self.is_at_end():
            token = self.current_token()
            
            if token.type == TokenType.NEWLINE:
                if (self.pos + 1 < len(self.tokens) and 
                    self.tokens[self.pos + 1].type == TokenType.NEWLINE):
                    break
                else:
                    current_text += token.value
                    self.advance()
                    continue
            
            block_start_tokens = [
                TokenType.HEADER, TokenType.CODE_FENCE,
                TokenType.CONTAINER_START, TokenType.CONTAINER_END,
                TokenType.DOC_COMMENT_START, TokenType.DOC_DIRECTIVE,
                TokenType.CODE_KEYWORD, TokenType.BLOCK_START_THREE_COLON, 
                TokenType.BLOCK_END_THREE_COLON, TokenType.PERCENT_FENCE,
                TokenType.DEF_TERM, TokenType.EOF
            ]
            
            if token.type in block_start_tokens:
                break
            
            inline_role_tokens = [
                TokenType.LEAN_ROLE, TokenType.NAME_ROLE, TokenType.KEYWORD_ROLE,
                TokenType.TACTIC_ROLE, TokenType.OPTION_ROLE, TokenType.TODO_ROLE,
                TokenType.TECH_ROLE, TokenType.REF_ROLE, 
                TokenType.INCLUDE_DIRECTIVE, TokenType.DOCSTRING_PLACEHOLDER
            ]
            
            if token.type in inline_role_tokens:
                flush_text()
                children.append({
                    "type": "InlineRole",
                    "role_type": token.type.name,
                    "content": token.value,
                    "translatable": False
                })
                self.advance()
            else:
                current_text += token.value
                self.advance()
        
        flush_text()
        
        if children:
            return {"type": "Paragraph", "content": children}
        return None

    def parse_doc_comment(self) -> Dict[str, Any]:
        self.advance()
        content = ""
        while not self.is_at_end() and self.current_token().type != TokenType.DOC_COMMENT_END:
            content += self.current_token().value
            self.advance()
        if not self.is_at_end(): self.advance()
        return {"type": "DocComment", "original": content.strip(), "translated": ""}

    def parse_doc_directive(self) -> Dict[str, Any]:
        """解析 #doc 指令，提取双引号内的可翻译内容。"""
        content = self.current_token().value
        self.advance()
        
        import re
        match = re.search(r'"([^"]*)"', content)
        if match:
            original_text = match.group(1)
            return {
                "type": "DocDirective",
                "original": original_text,
                "translated": "",
                "full_content": content
            }
        
        return {"type": "DocDirective", "original": "", "translated": "", "full_content": content}

    def parse_code_keyword(self) -> Dict[str, Any]:
        content = self.current_token().value
        self.advance()
        return {"type": "CodeLine", "content": content, "translatable": False}

    def parse_metadata_block(self) -> Dict[str, Any]:
        """解析 %%% ... %%% 元数据块，使用状态机思想处理多行。"""
        self.advance()
        
        content_lines = []
        while not self.is_at_end() and self.current_token().type != TokenType.PERCENT_FENCE:
            content_lines.append(self.current_token().value)
            self.advance()
        
        if not self.is_at_end() and self.current_token().type == TokenType.PERCENT_FENCE:
            self.advance()
        
        content = "".join(content_lines).strip()
        
        return {
            "type": "MetadataBlock",
            "content": content,
            "translatable": False
        }

    def parse_container_block(self) -> Dict[str, Any]:
        """
        解析 :::: 开头的容器，改进以区分指令和标题。
        """
        start_token = self.current_token()
        self.advance()
        
        content_raw = start_token.value.strip()[4:].strip()
        
        title = ""
        directives = []
        
        known_directives = ["keepEnv", "resetEnv", "autoImplicit", "hideProofs"]
        
        if content_raw in known_directives:
            directives.append(content_raw)
        elif content_raw.lower().startswith("example"):
            title_part = content_raw[len("example"):].strip().strip('"')
            title = title_part
        else:
            parts = content_raw.split()
            for part in parts:
                if part in known_directives:
                    directives.append(part)
                else:
                    if not title:
                        title = part.strip('"')

        children = []
        while not self.is_at_end() and self.current_token().type != TokenType.CONTAINER_END:
            while not self.is_at_end() and self.current_token().type == TokenType.NEWLINE:
                self.advance()
            if self.is_at_end() or self.current_token().type == TokenType.CONTAINER_END: 
                break
            
            node = self.parse_block()
            if node:
                children.append(node)
            else:
                self.advance()

        if not self.is_at_end() and self.current_token().type == TokenType.CONTAINER_END:
            self.advance()

        result = {
            "type": "ContainerBlock",
            "children": children
        }
        
        if title:
            result["title"] = {"original": title, "translated": ""}
        
        if directives:
            result["directives"] = directives
        
        return result

    def parse_simple_block(self) -> Dict[str, Any]:
        """
        统一处理所有非'show :='的 ::: 块，并解析参数。
        修复：改进参数解析逻辑以正确处理复杂格式。
        """
        start_token = self.current_token()
        self.advance()

        block_content = start_token.value.strip()[3:].strip()
        
        params = {}
        block_type = ""
        title = ""
        
        parts = block_content.split(None, 1)
        if parts:
            block_type = parts[0]
            remaining = parts[1] if len(parts) > 1 else ""
        else:
            block_type = "unknown"
            remaining = ""
        
        if remaining:
            param_start = remaining.find('(')
            param_end = remaining.rfind(')')
            
            if param_start != -1 and param_end != -1 and param_end > param_start:
                param_str = remaining[param_start + 1:param_end]
                
                title_before = remaining[:param_start].strip().strip('"')
                title_after = remaining[param_end + 1:].strip().strip('"')
                
                title = title_after if title_after else title_before
                
                self._parse_params(param_str, params)
                
            else:
                title = remaining.strip().strip('"')
        
        children = []
        while not self.is_at_end() and self.current_token().type != TokenType.BLOCK_END_THREE_COLON:
            while not self.is_at_end() and self.current_token().type == TokenType.NEWLINE:
                self.advance()
            
            if self.is_at_end() or self.current_token().type == TokenType.BLOCK_END_THREE_COLON: 
                break

            node = self.parse_block()
            if node:
                children.append(node)
            else:
                self.advance()
        
        if not self.is_at_end() and self.current_token().type == TokenType.BLOCK_END_THREE_COLON:
            self.advance()

        return {
            "type": "SimpleBlock", 
            "block_type": block_type, 
            "title": {"original": title, "translated": ""}, 
            "params": params,
            "children": children
        }
    
    def _parse_params(self, param_str: str, params: Dict[str, str]):
        """
        解析参数字符串，处理复杂的键值对格式。
        支持格式: key := "value", key := value, key := "quoted value with spaces"
        """
        param_pattern = r'(\w+)\s*:=\s*(?:"([^"]*)"|(\S+))'
        
        for match in re.finditer(param_pattern, param_str):
            key = match.group(1).strip()
            value = match.group(2) if match.group(2) is not None else match.group(3)
            if value:
                params[key] = value.strip()

# 保持向后兼容的类别名
# 注意：这个别名主要用于从旧代码迁移，新代码应直接使用 SyntaxParser
Parser = SyntaxParser