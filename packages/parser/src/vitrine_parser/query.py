"""Lexer, recursive descent parser, and filter AST compiler."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenKind(Enum):
    AND = auto()
    OR = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    IDENT = auto()
    STRING = auto()
    COLON = auto()
    COMPARE = auto()
    EOF = auto()


@dataclass
class Token:
    kind: TokenKind
    value: str
    pos: int


class Lexer:
    KEYWORDS = {"AND": TokenKind.AND, "OR": TokenKind.OR, "NOT": TokenKind.NOT}
    COMPARE_OPS = {">=", "<=", "!=", "==", ">", "<", "="}

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def _peek(self) -> str | None:
        return self.text[self.pos] if self.pos < len(self.text) else None

    def _advance(self) -> str | None:
        ch = self._peek()
        if ch is not None:
            self.pos += 1
        return ch

    def _skip_ws(self) -> None:
        while self._peek() is not None and self._peek() in " \t\n\r":
            self._advance()

    def next_token(self) -> Token:
        self._skip_ws()
        start = self.pos
        ch = self._peek()
        if ch is None:
            return Token(TokenKind.EOF, "", start)
        if ch == "(":
            self._advance()
            return Token(TokenKind.LPAREN, "(", start)
        if ch == ")":
            self._advance()
            return Token(TokenKind.RPAREN, ")", start)
        if ch == ":":
            self._advance()
            return Token(TokenKind.COLON, ":", start)
        if ch in "\"'":
            quote = self._advance()
            buf: list[str] = []
            while self._peek() is not None and self._peek() != quote:
                buf.append(self._advance() or "")
            if self._peek() == quote:
                self._advance()
            return Token(TokenKind.STRING, "".join(buf), start)
        # Compare or ident
        two = self.text[self.pos : self.pos + 2]
        if two in self.COMPARE_OPS:
            self.pos += 2
            return Token(TokenKind.COMPARE, two, start)
        if ch in "<>=!":
            self._advance()
            return Token(TokenKind.COMPARE, ch, start)
        if ch.isdigit() or (ch == "." and self.pos + 1 < len(self.text) and self.text[self.pos + 1].isdigit()):
            buf = []
            while self._peek() is not None and (self._peek().isdigit() or self._peek() == "."):
                buf.append(self._advance() or "")
            return Token(TokenKind.IDENT, "".join(buf), start)
        if ch.isalpha() or ch == "_":
            buf = []
            while self._peek() is not None and (self._peek().isalnum() or self._peek() in "._-"):
                buf.append(self._advance() or "")
            word = "".join(buf)
            kind = self.KEYWORDS.get(word.upper(), TokenKind.IDENT)
            return Token(kind, word, start)
        raise SyntaxError(f"Unexpected character {ch!r} at {start}")


def tokenize(text: str) -> list[Token]:
    lexer = Lexer(text)
    tokens: list[Token] = []
    while True:
        tok = lexer.next_token()
        tokens.append(tok)
        if tok.kind == TokenKind.EOF:
            break
    return tokens


# --- AST ---

@dataclass
class FilterNode:
    node_type: str
    field: str | None = None
    op: str | None = None
    value: Any = None
    children: list["FilterNode"] | None = None


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.i = 0

    def _cur(self) -> Token:
        return self.tokens[self.i]

    def _eat(self, kind: TokenKind | None = None) -> Token:
        tok = self._cur()
        if kind and tok.kind != kind:
            raise SyntaxError(f"Expected {kind}, got {tok.kind} at {tok.pos}")
        self.i += 1
        return tok

    def parse(self) -> FilterNode:
        node = self._or_expr()
        if self._cur().kind != TokenKind.EOF:
            raise SyntaxError(f"Unexpected token {self._cur().value!r}")
        return node

    def _or_expr(self) -> FilterNode:
        left = self._not_expr()
        while self._cur().kind == TokenKind.OR:
            self._eat(TokenKind.OR)
            right = self._and_expr()
            left = FilterNode(node_type="or", children=[left, right])
        return left

    def _and_expr(self) -> FilterNode:
        left = self._not_expr()
        while self._cur().kind == TokenKind.AND:
            self._eat(TokenKind.AND)
            right = self._not_expr()
            left = FilterNode(node_type="and", children=[left, right])
        return left

    def _not_expr(self) -> FilterNode:
        if self._cur().kind == TokenKind.NOT:
            self._eat(TokenKind.NOT)
            child = self._not_expr()
            return FilterNode(node_type="not", children=[child])
        return self._primary()

    def _primary(self) -> FilterNode:
        if self._cur().kind == TokenKind.LPAREN:
            self._eat(TokenKind.LPAREN)
            node = self._or_expr()
            self._eat(TokenKind.RPAREN)
            return node
        field = self._eat(TokenKind.IDENT).value
        if self._cur().kind == TokenKind.COLON:
            self._eat(TokenKind.COLON)
            val_tok = self._eat()
            if val_tok.kind not in (TokenKind.STRING, TokenKind.IDENT):
                raise SyntaxError("Expected value after colon")
            return FilterNode(node_type="match", field=field, op=":", value=val_tok.value)
        op = self._eat(TokenKind.COMPARE).value
        val_tok = self._eat()
        if val_tok.kind == TokenKind.STRING:
            value: Any = val_tok.value
        elif val_tok.kind == TokenKind.IDENT:
            try:
                value = float(val_tok.value) if "." in val_tok.value else int(val_tok.value)
            except ValueError:
                value = val_tok.value
        else:
            raise SyntaxError("Expected value after compare")
        return FilterNode(node_type="compare", field=field, op=op, value=value)


def parse_query(text: str) -> FilterNode:
    return Parser(tokenize(text)).parse()


def compile_filter(ast: FilterNode) -> dict[str, Any]:
    """Compile AST to a JSON-serializable filter dict."""
    if ast.node_type == "and":
        assert ast.children
        return {"and": [compile_filter(c) for c in ast.children]}
    if ast.node_type == "or":
        assert ast.children
        return {"or": [compile_filter(c) for c in ast.children]}
    if ast.node_type == "not":
        assert ast.children
        return {"not": compile_filter(ast.children[0])}
    if ast.node_type == "match":
        return {"field": ast.field, "op": "match", "value": ast.value}
    if ast.node_type == "compare":
        return {"field": ast.field, "op": ast.op, "value": ast.value}
    raise ValueError(f"Unknown node type {ast.node_type}")
