#!/usr/bin/env python3
"""
Lean Parser Test Suite
Tests tokenizer and syntax_parser functionality for Lean documentation.
"""

import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from parser_new.tokenizer import Tokenizer
from parser_new.syntax_parser import SyntaxParser

class LeanParserTester:
    def __init__(self, output_dir="test_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def test_file(self, input_file: str, test_name: str = None):
        """Test parsing of a single file"""
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"Error: File not found {input_file}")
            return False
            
        if test_name is None:
            test_name = input_path.stem
            
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Tokenize
            tokenizer = Tokenizer()
            tokens = tokenizer.tokenize(content)
            
            # Parse
            parser = SyntaxParser(tokens)
            ast = parser.parse()
            
            # Save results
            self._save_results(test_name, content, tokens, ast)
            print(f"✓ Test completed: {test_name}")
            return True
            
        except Exception as e:
            print(f"✗ Test failed: {test_name} - {str(e)}")
            return False
    
    def _save_results(self, test_name: str, content: str, tokens, ast):
        """Save test results to files"""
        test_dir = self.output_dir / test_name
        test_dir.mkdir(exist_ok=True)
        
        # Save input
        with open(test_dir / "input.md", 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save tokens
        tokens_data = []
        for token in tokens:
            tokens_data.append({
                "type": token.type.name,
                "value": repr(token.value),
                "line": token.line,
                "column": token.column
            })
        
        with open(test_dir / "tokens.json", 'w', encoding='utf-8') as f:
            json.dump(tokens_data, f, indent=2, ensure_ascii=False)
        
        # Save AST
        with open(test_dir / "ast.json", 'w', encoding='utf-8') as f:
            json.dump(ast, f, indent=2, ensure_ascii=False)
        
        # Generate report
        self._generate_report(test_dir, content, tokens, ast)
    
    def _generate_report(self, test_dir: Path, content: str, tokens, ast):
        """Generate readable test report"""
        with open(test_dir / "report.txt", 'w', encoding='utf-8') as f:
            f.write("=== LEAN PARSER TEST REPORT ===\n\n")
            
            # Statistics
            f.write("Statistics:\n")
            f.write(f"- Content length: {len(content)} characters\n")
            f.write(f"- Total tokens: {len(tokens)}\n")
            f.write(f"- AST nodes: {len(ast)}\n\n")
            
            # Token type counts
            token_counts = {}
            for token in tokens:
                token_type = token.type.name
                token_counts[token_type] = token_counts.get(token_type, 0) + 1
            
            f.write("Token types:\n")
            for token_type, count in sorted(token_counts.items()):
                f.write(f"- {token_type}: {count}\n")
            f.write("\n")
            
            # Inline roles detection
            inline_roles = [token for token in tokens 
                          if token.type.name.endswith('_ROLE') or 
                             token.type.name in ['INCLUDE_DIRECTIVE', 'DOCSTRING_PLACEHOLDER']]
            
            if inline_roles:
                f.write("Inline roles detected:\n")
                for token in inline_roles:
                    f.write(f"- {token.type.name}: {repr(token.value)} (line {token.line})\n")
                f.write("\n")
            
            # AST node type counts
            def count_ast_nodes(nodes, counts=None):
                if counts is None:
                    counts = {}
                for node in nodes:
                    if isinstance(node, dict) and 'type' in node:
                        node_type = node['type']
                        counts[node_type] = counts.get(node_type, 0) + 1
                        if 'children' in node:
                            count_ast_nodes(node['children'], counts)
                        if 'content' in node and isinstance(node['content'], list):
                            count_ast_nodes(node['content'], counts)
                return counts
            
            ast_counts = count_ast_nodes(ast)
            f.write("AST node types:\n")
            for node_type, count in sorted(ast_counts.items()):
                f.write(f"- {node_type}: {count}\n")
            f.write("\n")
            
            # Code blocks with parameters
            def find_code_blocks(nodes):
                blocks = []
                for node in nodes:
                    if isinstance(node, dict):
                        if node.get('type') == 'CodeBlock' and node.get('params'):
                            blocks.append(node)
                        if 'children' in node:
                            blocks.extend(find_code_blocks(node['children']))
                return blocks
            
            code_blocks = find_code_blocks(ast)
            if code_blocks:
                f.write("Code blocks with parameters:\n")
                for i, block in enumerate(code_blocks):
                    f.write(f"- Block {i+1}: language={block.get('language')}, params={block.get('params')}\n")
                f.write("\n")
            
            # Definition lists
            def find_definition_lists(nodes):
                def_lists = []
                for node in nodes:
                    if isinstance(node, dict):
                        if node.get('type') == 'DefinitionList':
                            def_lists.append(node)
                        if 'children' in node:
                            def_lists.extend(find_definition_lists(node['children']))
                return def_lists
            
            def_lists = find_definition_lists(ast)
            if def_lists:
                f.write("Definition lists:\n")
                for i, def_list in enumerate(def_lists):
                    f.write(f"- List {i+1}: {len(def_list.get('definitions', []))} definitions\n")
                f.write("\n")
            
            # Container blocks
            def find_container_blocks(nodes):
                containers = []
                for node in nodes:
                    if isinstance(node, dict):
                        if node.get('type') == 'ContainerBlock':
                            containers.append(node)
                        if 'children' in node:
                            containers.extend(find_container_blocks(node['children']))
                return containers
            
            containers = find_container_blocks(ast)
            if containers:
                f.write("Container blocks:\n")
                for i, container in enumerate(containers):
                    title = container.get('title', {}).get('original', 'No title')
                    directives = container.get('directives', [])
                    f.write(f"- Container {i+1}: title='{title}', directives={directives}\n")
    
    def create_sample_test_files(self):
        """Create sample test files for development"""
        samples_dir = self.output_dir / "samples"
        samples_dir.mkdir(exist_ok=True)
        
        # Sample 1: Basic Lean roles
        sample1 = """# Lean Roles Test

Text with {lean}`Array` and {lean type:="Nat → Prop"}`theorem`.

Also {name}`MyTheorem` and {keyword}`simp` keyword.

{tactic}`rw` is a tactic, {option}`autoImplicit` is an option.

{TODO}[Add more examples]

{tech}[Mathematical induction] is important.

{deftech}_linearly_ is technical term format.

See {ref "array-syntax"}[array literal syntax] for details.

```lean (name := "example1", keep := true)
theorem example_theorem : 1 + 1 = 2 := by simp
```

::: example (name := "basic_example") "Basic Example"
This is an example block.
:::
"""
        
        # Sample 2: Complex document structure
        sample2 = """# Complex Document Test

{include library.lean}

## Definitions

{docstring MyFunction}

::: definition (formal := true) "Function Definition"
```lean (name := "my_function")
def myFunction (n : Nat) : Nat := n + 1
```
:::

## Theorems

Important {lean type:="Nat → Nat → Prop"}`theorem` proof.

Understanding {name}`Array.mk` function is crucial.

```lean (name := "main_theorem", keep := true, formal := true)  
theorem main_theorem (n m : Nat) : n + m = m + n := by
  rw [Nat.add_comm]
```

{TODO}[Verify proof correctness]

%%%
title: "Lean Mathematics Foundation"
author: "Test User"  
date: "2024"
%%%
"""
        
        # Sample 3: Inline roles and block parameters
        sample3 = """# Inline Roles and Block Parameters Test

## Backtick Format
- {lean}`Array`
- {name}`MyFunction`
- {keyword}`simp`

## Bracket Format
- {tech}[mathematical induction]
- {deftech}[linear algorithm]
- {ref "example"}[reference example]

## Underscore Format
- {deftech}_linearly_
- {deftech}_efficiently_

## Block Parameters
::: syntax term (title := "Array Literals")
Array literal syntax definition.
:::

::: example (name := "complex_example", formal := true) "Complex Example"
Example with multiple parameters.
:::
"""
        
        # Sample 4: Semantic structures
        sample4 = """# Semantic Structure Test

## Definition Lists

: size
  Number of elements in the array.

: capacity  
  Maximum number of elements without reallocation.

: push
  Add element using {name}`Array.push`.

## Container Directives

:::: keepEnv
This is a keepEnv directive container.
::::

:::: example "Array Operations"
Example container with title.
::::

## Mixed Test

: append
  Concatenate arrays using {lean}`Array.append`. 
  This is {deftech}_linear_ operation.

:::: example "Performance Example"
Arrays are efficient when used {deftech}_linearly_.

: time_complexity
  O(n) for most operations.
::::
"""
        
        samples = [
            ("lean_roles_test.md", sample1),
            ("complex_lean_doc.md", sample2), 
            ("inline_roles_test.md", sample3),
            ("semantic_structure_test.md", sample4)
        ]
        
        sample_files = []
        for filename, content in samples:
            file_path = samples_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            sample_files.append(file_path)
        
        return sample_files

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lean Parser Test Tool")
    parser.add_argument("input_file", nargs="?", help="Input file path to test")
    parser.add_argument("--output-dir", default="test_output", help="Output directory")
    parser.add_argument("--create-samples", action="store_true", help="Create sample test files")
    parser.add_argument("--test-samples", action="store_true", help="Test created sample files")
    
    args = parser.parse_args()
    
    tester = LeanParserTester(args.output_dir)
    
    if args.create_samples:
        sample_files = tester.create_sample_test_files()
        print(f"Sample files created in: {tester.output_dir / 'samples'}")
        
        if args.test_samples:
            print("Testing sample files...")
            for sample_file in sample_files:
                tester.test_file(str(sample_file))
    
    elif args.input_file:
        tester.test_file(args.input_file)
    
    else:
        print("Usage:")
        print("  python test_lean_parser.py <input_file>")
        print("  python test_lean_parser.py --create-samples --test-samples")

if __name__ == "__main__":
    main()
