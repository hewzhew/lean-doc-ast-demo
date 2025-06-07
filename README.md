# Lean Documentation AST Parser Demo

This project demonstrates how to extract an Abstract Syntax Tree (AST) from Lean 4 documentation files, specifically designed for automated translation workflows.

## Project Overview

The parser can handle complex syntax structures in Lean 4 documentation, including:
- Documentation comments and directives
- Code blocks and inline code
- Container blocks and metadata blocks
- Inline role markers (such as `{lean}`, `{name}`, `{tech}`, etc.)
- Definition lists
- Various block-level and inline syntax elements

## Test File Source

The `Array.lean` file used for testing in this project is sourced from the official Lean 4 Reference Manual repository:
- **Source**: [leanprover/reference-manual](https://github.com/leanprover/reference-manual/blob/main/Manual/BasicTypes/Array.lean)
- **File**: Manual/BasicTypes/Array.lean

We gratefully acknowledge the Lean community and contributors for providing this comprehensive documentation example that serves as an excellent test case for our parser.

## Quick Start

### Requirements

- Python 3.7+
- No external dependencies (uses Python standard library only)

### Basic Usage

Use the `Array.lean` file in the project as a test example:

```bash
python test_lean_parser.py Array.lean --output-dir test_results
```

### Command Line Options

```bash
# Test a single file
python test_lean_parser.py <input_file> [options]

# Create sample test files
python test_lean_parser.py --create-samples --test-samples --output-dir my_output

# Create sample files only (without running tests)
python test_lean_parser.py --create-samples --output-dir my_output
```

#### Parameter Description

- `input_file`: Path to the Lean documentation file to parse
- `--output-dir`: Specify output directory (default: test_output)
- `--create-samples`: Create sample test files
- `--test-samples`: Test the created sample files

### Testing Array.lean Example

```bash
# Basic test
python test_lean_parser.py Array.lean

# Specify output directory
python test_lean_parser.py Array.lean --output-dir array_analysis

# Detailed analysis output
python test_lean_parser.py Array.lean --output-dir detailed_output
```

## Output Files Description

After testing is complete, the output directory will contain the following files:

```
test_results/
├── Array/                    # Directory named after input file
│   ├── input.md             # Original input content
│   ├── tokens.json          # Lexical analysis results (token list)
│   ├── ast.json             # Syntax analysis results (AST tree)
│   └── report.txt           # Human-readable analysis report
```

### Output Files Details

#### 1. tokens.json
Contains all tokens identified during lexical analysis:
```json
[
  {
    "type": "DOC_DIRECTIVE",
    "value": "#doc (Manual) \"Arrays\" =>",
    "line": 15,
    "column": 0
  }
]
```

#### 2. ast.json  
Contains the complete abstract syntax tree structure:
```json
[
  {
    "type": "DocDirective", 
    "original": "Arrays",
    "translated": "",
    "full_content": "#doc (Manual) \"Arrays\" =>"
  }
]
```

#### 3. report.txt
Provides detailed analysis statistics:
- Content length and token statistics
- Token type counts
- Inline role detection results
- AST node type distribution
- Code block parameter analysis
- Definition list and container block statistics

## Supported Lean Syntax Features

### Inline Role Markers
- `{lean}`...`` - Lean code references
- `{name}`...`` - Name references  
- `{keyword}`...`` - Keywords
- `{tactic}`...`` - Tactics
- `{tech}[...]` - Technical terms
- `{deftech}_..._ ` - Definition terms
- `{ref "..."}[...]` - Cross-references

### Block-level Structures
- `:::` Simple blocks (syntax, examples, etc.)
- `::::` Container blocks (keepEnv, example, etc.)
- `%%%` Metadata blocks
- Code fences (with parameter support)
- Definition lists (`: term` format)

### Special Directives
- `#doc` Documentation directives
- `{include ...}` Include directives
- `{docstring ...}` Docstring placeholders

## Example Usage Scenarios

### 1. Analyze Existing Lean Documentation
```bash
python test_lean_parser.py Array.lean --output-dir array_analysis
```

### 2. Batch Test Sample Files
```bash
python test_lean_parser.py --create-samples --test-samples --output-dir batch_test
```

### 3. Development and Debugging
```bash
# Create test samples for development
python test_lean_parser.py --create-samples --output-dir dev_samples
# Then test specific samples
python test_lean_parser.py dev_samples/samples/lean_roles_test.md
```

## Project Structure

```
lean-doc-ast-demo-main/
├── parser_new/
│   ├── tokenizer.py         # Lexical analyzer
│   └── syntax_parser.py     # Syntax analyzer
├── Array.lean               # Test Lean documentation
├── test_lean_parser.py      # Main test script
├── README.md               # Chinese documentation
└── README_EN.md            # This English documentation
```

## Development and Contributing

### Core Components

1. **Tokenizer (Lexical Analyzer)**: Breaks raw text into tokens
2. **SyntaxParser (Syntax Analyzer)**: Builds AST tree structure
3. **Test Framework**: Provides complete testing and analysis functionality

### Extending the Parser

To add support for new syntax:

1. Add new TokenType and recognition patterns in `tokenizer.py`
2. Add corresponding parsing methods in `syntax_parser.py`
3. Update test cases to verify functionality

### Debugging Tips

1. Check `tokens.json` to verify lexical analysis is correct
2. Examine `ast.json` to validate syntax tree structure
3. Read `report.txt` for statistics and potential issues

## Frequently Asked Questions

**Q: What to do when parsing fails?**
A: Check input file encoding (should be UTF-8), and review the generated report.txt for detailed error information.

**Q: How to handle new Lean syntax?**
A: First run the existing parser to see unrecognized content, then add corresponding patterns in the tokenizer.

**Q: What if output files are too large?**
A: You can modify the output options in test_lean_parser.py to generate only the needed files.

## License

This project is released under the Apache 2.0 license.
