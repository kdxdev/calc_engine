# CALC ENGINE

A self-contained, production-grade mathematical expression evaluator written in clean, native Python. The engine transforms raw input strings into distinct linear tokens, builds an Abstract Syntax Tree (AST) through a structural Recursive Descent Parser, and executes calculations utilizing the Visitor architectural pattern.

## Key Architectural Highlights
* **Zero Dependencies:** Implemented purely in vanilla Python using standard type hinting structures.
* **PEMDAS Rigor:** Correctly structures operational precedence hierarchies, safely routing unary sign negations, complex groupings, and right-associative power operators (`**`).
* **Isolated Error Flow:** Features custom exceptions (`LexError`, `ParseError`, `EvalError`) to gracefully isolate formatting problems or numerical errors without crashing the thread context.

---

## Installation & Setup
No installations or package configurations are needed. Drop the script into your working environment and launch directly using Python:

```bash
python3 math_ast.py

# MADE BY KODEX
