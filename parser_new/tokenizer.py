# parser_new/tokenizer.py

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List

class TokenType(Enum):
    """定义了我们能识别的所有词元类型。"""
    EOF = auto()
    TEXT = auto()
    NEWLINE = auto()
    DOC_COMMENT_START = auto()
    DOC_COMMENT_END = auto()
    HEADER = auto()
    CODE_FENCE = auto()
    DOC_DIRECTIVE = auto()
    CODE_KEYWORD = auto()
    PERCENT_FENCE = auto()

    # 重新排序：结束标记在开始标记之前
    CONTAINER_END = auto()           # :::: 单独一行
    CONTAINER_START = auto()         # :::: 开头的行
    BLOCK_END_THREE_COLON = auto()   # ::: 单独一行
    BLOCK_START_THREE_COLON = auto() # 所有 ::: 开头的行

    # 新增：特殊指令类型
    INCLUDE_DIRECTIVE = auto()       # {include ...}
    DOCSTRING_PLACEHOLDER = auto()   # {docstring ...}

    # 新增：内联标记角色类型
    LEAN_ROLE = auto()              # {lean ...}`...`
    NAME_ROLE = auto()              # {name ...}`...`
    KEYWORD_ROLE = auto()           # {keyword ...}`...`
    TACTIC_ROLE = auto()            # {tactic}`...`
    OPTION_ROLE = auto()            # {option}`...`
    TODO_ROLE = auto()              # {TODO}[...]
    TECH_ROLE = auto()              # {tech}[...] or {deftech}[...]
    REF_ROLE = auto()               # {ref "..."}[...]

    # 新增：定义列表支持
    DEF_TERM = auto()               # : term_name

    # 行内标记
    UNDERSCORE = auto()
    ASTERISK = auto()
    BACKTICK = auto()
    L_BRACKET = auto()
    R_BRACKET = auto()
    L_PAREN = auto()
    R_PAREN = auto()

@dataclass
class Token:
    """定义了单个词元的数据结构。"""
    type: TokenType
    value: str
    line: int
    column: int


class Tokenizer:
    """词法分析器类，负责将文本转换为词元序列"""
    
    def __init__(self):
        # 统一的 token 规范列表 - 按优先级排序
        self.token_specification = [
            # 块级模式 - 必须在行首
            ('CONTAINER_END',           r'^::::\s*$'),
            ('CONTAINER_START',         r'^::::\s*\w+.*'),
            ('BLOCK_END_THREE_COLON',   r'^:::\s*$'),
            ('BLOCK_START_THREE_COLON', r'^:::\s*.*'),
            ('PERCENT_FENCE',           r'^%%%\s*$'),
            ('DOC_DIRECTIVE',           r'^#doc\s+.*'),
            ('CODE_KEYWORD',            r'^(import|open|set_option|variable|example|def|theorem|lemma|namespace|end|section)\b.*'),
            ('DOC_COMMENT_START',       r'^\s*/-'),
            ('DOC_COMMENT_END',         r'^\s*-/'),
            ('HEADER',                  r'^#+'),
            ('CODE_FENCE',              r'^```.*'),
            
            # 定义列表模式 - 必须在行首
            ('DEF_TERM',                r'^:\s+\w+.*'),
            
            # 内联角色模式 - 修复以支持所有格式变体
            # 反引号类型的角色: {role}`content`
            ('LEAN_ROLE',               r'\{lean(?:\s+type:="[^"]*")?\}`[^`]*`'),
            ('NAME_ROLE',               r'\{name(?:\s+[^}]+)?\}`[^`]*`'),
            ('KEYWORD_ROLE',            r'\{keyword(?:Of\s+\w+)?\}`[^`]*`'),
            ('TACTIC_ROLE',             r'\{tactic\}`[^`]*`'),
            ('OPTION_ROLE',             r'\{option\}`[^`]*`'),
            
            # 方括号类型的角色: {role}[content]
            ('REF_ROLE',                r'\{ref\s+"[^"]*"\}\[[^\]]*\]'),
            ('TODO_ROLE',               r'\{TODO\}\[[^\]]*\]'),
            
            # TECH_ROLE 的多种格式 - 修复关键问题
            # 1. {tech}[content] 格式
            # 2. {deftech}[content] 格式  
            # 3. {deftech}_content_ 格式 (这是缺失的!)
            ('TECH_ROLE',               r'\{(?:def)?tech\}(?:\[[^\]]*\]|_[^_]*_)'),
            
            # 特殊指令
            ('INCLUDE_DIRECTIVE',       r'\{include\s+[^}]+\}'),
            ('DOCSTRING_PLACEHOLDER',   r'\{docstring\s+[^}]+\}'),
            
            # 其他
            ('NEWLINE',                 r'\n'),
            ('TEXT',                    r'.+?'),  # 非贪婪匹配，放在最后
        ]
        
        self.tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.token_specification)
    
    def tokenize(self, text: str) -> List[Token]:
        """
        词法分析主方法：接收原始文本，返回词元列表。
        
        使用统一的正则表达式进行tokenization。
        """
        tokens = []
        line_num = 1
        line_start = 0
        
        for mo in re.finditer(self.tok_regex, text, re.MULTILINE):
            kind = mo.lastgroup
            value = mo.group()
            column = mo.start() - line_start
            
            if kind is None:
                continue
            
            token_type = TokenType[kind]
            tokens.append(Token(token_type, value, line_num, column))
            
            # 更新行号和行起始位置
            if kind == 'NEWLINE':
                line_num += 1
                line_start = mo.end()
                
        tokens.append(Token(TokenType.EOF, '', line_num, 0))
        return tokens


# 保持向后兼容的函数接口
def tokenize(text: str) -> List[Token]:
    """向后兼容的词法分析函数"""
    tokenizer = Tokenizer()
    return tokenizer.tokenize(text)