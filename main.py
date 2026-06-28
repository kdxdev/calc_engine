from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Union, List


class CalcError(Exception):
    pass
class LexError(CalcError):
    pass
class ParseError(CalcError):
    pass
class EvalError(CalcError):
    pass
class TokenType(Enum):
    NUMBER = auto()
    PLUS = auto()
    MINUS = auto()
    MUL = auto()
    DIV = auto()
    POW = auto()
    LPAREN = auto()
    RPAREN = auto()
    EOF = auto()
class Token:
    def __init__(self, ttype: TokenType, value: Optional[float], pos: int) -> None:
        self.type = ttype
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value}, pos={self.pos})"
SIMPLE_OPS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
}
class Lexer:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.n = len(text)
    def _cur(self) -> Optional[str]:
        return self.text[self.pos] if self.pos < self.n else None
    def _peek(self, off: int = 1) -> Optional[str]:
        p = self.pos + off
        return self.text[p] if p < self.n else None

    def _skip_ws(self) -> None:
        while self._cur() is not None and self._cur().isspace():
            self.pos += 1
    def _read_number(self) -> Token:
        start = self.pos
        dots = 0
        buf = ""
        while self._cur() is not None and (self._cur().isdigit() or self._cur() == "."):
            if self._cur() == ".":
                dots += 1
                if dots > 1:
                    raise LexError(f"malformed number near pos {start}")
            buf += self._cur()
            self.pos += 1
        try:
            val = float(buf)
        except ValueError:
            raise LexError(f"malformed number '{buf}' near pos {start}")
        return Token(TokenType.NUMBER, val, start)
    def get_next_token(self) -> Token:
        while self._cur() is not None:
            ch = self._cur()
            if ch.isspace():
                self._skip_ws()
                continue
            if ch.isdigit() or ch == ".":
                return self._read_number()
            if ch == "*":
                if self._peek() == "*":
                    p = self.pos
                    self.pos += 2
                    return Token(TokenType.POW, "**", p)
                p = self.pos
                self.pos += 1
                return Token(TokenType.MUL, "*", p)
            if ch == "/":
                p = self.pos
                self.pos += 1
                return Token(TokenType.DIV, "/", p)
            if ch in SIMPLE_OPS:
                p = self.pos
                self.pos += 1
                return Token(SIMPLE_OPS[ch], ch, p)
            raise LexError(f"unexpected character '{ch}' at pos {self.pos}")
        return Token(TokenType.EOF, None, self.pos)


class ASTNode:
    pass

@dataclass
class NumberNode(ASTNode):
    value: float
@dataclass
class UnaryOpNode(ASTNode):
    op: TokenType
    operand: ASTNode

@dataclass
class BinOpNode(ASTNode):
    left: ASTNode
    op: TokenType
    right: ASTNode
class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer = lexer
        self.tok = self.lexer.get_next_token()

    def _eat(self, ttype: TokenType) -> Token:
        if self.tok.type != ttype:
            raise ParseError(f"expected {ttype} but got {self.tok.type} at pos {self.tok.pos}")
        old = self.tok
        self.tok = self.lexer.get_next_token()
        return old

    def primary(self) -> ASTNode:
        t = self.tok
        if t.type == TokenType.NUMBER:
            self._eat(TokenType.NUMBER)
            return NumberNode(t.value)
        if t.type == TokenType.LPAREN:
            self._eat(TokenType.LPAREN)
            node = self.expr()
            self._eat(TokenType.RPAREN)
            return node
        raise ParseError(f"unexpected token {t.type} at pos {t.pos}")
    def power(self) -> ASTNode:
        base = self.primary()
        if self.tok.type == TokenType.POW:
            self._eat(TokenType.POW)
            exponent = self.unary()
            return BinOpNode(base, TokenType.POW, exponent)
        return base

    def unary(self) -> ASTNode:
        t = self.tok
        if t.type in (TokenType.PLUS, TokenType.MINUS):
            self._eat(t.type)
            return UnaryOpNode(t.type, self.unary())
        return self.power()

    def term(self) -> ASTNode:
        node = self.unary()
        while self.tok.type in (TokenType.MUL, TokenType.DIV):
            op = self.tok.type
            self._eat(op)
            node = BinOpNode(node, op, self.unary())
        return node
    def expr(self) -> ASTNode:
        node = self.term()
        while self.tok.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.tok.type
            self._eat(op)
            node = BinOpNode(node, op, self.term())
        return node

    def parse(self) -> ASTNode:
        node = self.expr()
        if self.tok.type != TokenType.EOF:
            raise ParseError(f"trailing garbage at pos {self.tok.pos}")
        return node

class Interpreter:
    def visit(self, node: ASTNode) -> float:
        name = f"visit_{type(node).__name__}"
        fn = getattr(self, name, None)
        if fn is None:
            raise EvalError(f"no visitor for node type {type(node).__name__}")
        return fn(node)

    def visit_NumberNode(self, node: NumberNode) -> float:
        return node.value

    def visit_UnaryOpNode(self, node: UnaryOpNode) -> float:
        v = self.visit(node.operand)
        if node.op == TokenType.MINUS:
            return -v
        if node.op == TokenType.PLUS:
            return v
        raise EvalError(f"bad unary op {node.op}")

    def visit_BinOpNode(self, node: BinOpNode) -> float:
        l = self.visit(node.left)
        r = self.visit(node.right)
        if node.op == TokenType.PLUS:
            return l + r
        if node.op == TokenType.MINUS:
            return l - r
        if node.op == TokenType.MUL:
            return l * r
        if node.op == TokenType.DIV:
            if r == 0:
                raise EvalError("division by zero")
            return l / r
        if node.op == TokenType.POW:
            try:
                return l ** r
            except OverflowError:
                raise EvalError("exponent overflow")
        raise EvalError(f"unknown binary op {node.op}")

def evaluate(text: str) -> float:
    lexer = Lexer(text)
    parser = Parser(lexer)
    tree = parser.parse()
    interp = Interpreter()
    return interp.visit(tree)
def dump_tree(node: ASTNode, depth: int = 0) -> str:
    pad = "  " * depth
    if isinstance(node, NumberNode):
        return f"{pad}Num({node.value})"
    if isinstance(node, UnaryOpNode):
        return f"{pad}Unary({node.op.name})\n{dump_tree(node.operand, depth + 1)}"
    if isinstance(node, BinOpNode):
        left = dump_tree(node.left, depth + 1)
        right = dump_tree(node.right, depth + 1)
        return f"{pad}Bin({node.op.name})\n{left}\n{right}"
    return f"{pad}???"
def safe_eval(text: str) -> Union[float, str]:
    try:
        return evaluate(text)
    except CalcError as e:
        return f"ERROR: {e}"
if __name__ == "__main__":
    tests: List[str] = [
        "3 + (4 * 5) - 2.5",
        "2 ** 3 ** 2",
        "-2 ** 2",
        "(2 + 3) * (4 - 1) / 5",
        "10 / (2 - 2)",
        "3.5 * -2 + 7",
        "((1 + 2) * (3 + 4)) ** 2",
        "100 - 25 / 5 + 3 * (2 + 2)",
        "-(3 + 4) * 2",
        "1 / 3 + 1 / 3 + 1 / 3",
    ]
    for t in tests:
        res = safe_eval(t)
        print(f"{t!r:45} => {res}")
    print()
    sample = Parser(Lexer("(2 + 3) * 4 - 1"))
    tree = sample.parse()
    print(dump_tree(tree))
    print("result:", Interpreter().visit(tree))
