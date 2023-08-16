"""Simple policy DSL evaluator for rule expressions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class TokenKind(str, Enum):
    IDENT = "ident"
    NUMBER = "number"
    STRING = "string"
    OP = "op"
    LPAREN = "lparen"
    RPAREN = "rparen"
    AND = "and"
    OR = "or"
    NOT = "not"
    EOF = "eof"


@dataclass
class Token:
    kind: TokenKind
    value: str
    pos: int


@dataclass
class ASTNode:
    pass


@dataclass
class BinaryOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode


@dataclass
class Comparison(ASTNode):
    field: str
    operator: str
    value: Any


@dataclass
class Literal(ASTNode):
    value: Any


@dataclass
class ParseResult:
    ast: ASTNode
    tokens: list[Token]


class PolicyDSLError(Exception):
    pass


_TOKEN_PATTERN = re.compile(
    r'\s*(?:(?P<and>AND)|(?P<or>OR)|(?P<not>NOT)|'
    r"(?P<string>'[^']*'|\"[^\"]*\")|"
    r"(?P<number>-?\d+(?:\.\d+)?)|"
    r"(?P<op>=|!=|<>|>=|<=|>|<)|"
    r"(?P<lparen>\()|(?P<rparen>\))|"
    r"(?P<ident>[a-zA-Z_][a-zA-Z0-9_]*))"
)


def tokenize(expression: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    while pos < len(expression):
        match = _TOKEN_PATTERN.match(expression, pos)
        if not match:
            raise PolicyDSLError(f"unexpected character at {pos}: {repr(expression[pos])}")
        if match.group("and"):
            tokens.append(Token(TokenKind.AND, "AND", pos))
        elif match.group("or"):
            tokens.append(Token(TokenKind.OR, "OR", pos))
        elif match.group("not"):
            tokens.append(Token(TokenKind.NOT, "NOT", pos))
        elif match.group("string"):
            raw = match.group("string")
            tokens.append(Token(TokenKind.STRING, raw[1:-1], pos))
        elif match.group("number"):
            tokens.append(Token(TokenKind.NUMBER, match.group("number"), pos))
        elif match.group("op"):
            tokens.append(Token(TokenKind.OP, match.group("op"), pos))
        elif match.group("lparen"):
            tokens.append(Token(TokenKind.LPAREN, "(", pos))
        elif match.group("rparen"):
            tokens.append(Token(TokenKind.RPAREN, ")", pos))
        elif match.group("ident"):
            val = match.group("ident")
            upper = val.upper()
            if upper == "AND":
                tokens.append(Token(TokenKind.AND, "AND", pos))
            elif upper == "OR":
                tokens.append(Token(TokenKind.OR, "OR", pos))
            elif upper == "NOT":
                tokens.append(Token(TokenKind.NOT, "NOT", pos))
            else:
                tokens.append(Token(TokenKind.IDENT, val, pos))
        pos = match.end()
    tokens.append(Token(TokenKind.EOF, "", pos))
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _match(self, kind: TokenKind) -> bool:
        if self._peek().kind == kind:
            self._advance()
            return True
        return False

    def parse(self) -> ASTNode:
        node = self._parse_or()
        if self._peek().kind != TokenKind.EOF:
            raise PolicyDSLError(f"unexpected token {self._peek().value!r}")
        return node

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        while self._peek().kind == TokenKind.OR:
            self._advance()
            right = self._parse_and()
            left = BinaryOp("OR", left, right)
        return left

    def _parse_and(self) -> ASTNode:
        left = self._parse_not()
        while self._peek().kind == TokenKind.AND:
            self._advance()
            right = self._parse_not()
            left = BinaryOp("AND", left, right)
        return left

    def _parse_not(self) -> ASTNode:
        if self._match(TokenKind.NOT):
            return UnaryOp("NOT", self._parse_not())
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        if self._match(TokenKind.LPAREN):
            node = self._parse_or()
            if not self._match(TokenKind.RPAREN):
                raise PolicyDSLError("expected closing parenthesis")
            return node
        return self._parse_comparison()

    def _parse_comparison(self) -> ASTNode:
        field_tok = self._advance()
        if field_tok.kind != TokenKind.IDENT:
            raise PolicyDSLError(f"expected field name, got {field_tok.value!r}")
        if self._peek().kind != TokenKind.OP:
            return Comparison(field_tok.value, "=", True)
        op_tok = self._advance()
        val_tok = self._advance()
        value: Any
        if val_tok.kind == TokenKind.NUMBER:
            value = float(val_tok.value) if "." in val_tok.value else int(val_tok.value)
        elif val_tok.kind == TokenKind.STRING:
            value = val_tok.value
        elif val_tok.kind == TokenKind.IDENT:
            lower = val_tok.value.lower()
            if lower == "true":
                value = True
            elif lower == "false":
                value = False
            else:
                value = val_tok.value
        else:
            raise PolicyDSLError(f"expected value, got {val_tok.value!r}")
        return Comparison(field_tok.value, op_tok.value, value)


def parse_policy(expression: str) -> ParseResult:
    tokens = tokenize(expression)
    ast = _Parser(tokens).parse()
    return ParseResult(ast=ast, tokens=tokens)


def _compare(actual: Any, op: str, expected: Any) -> bool:
    if op in ("=", "=="):
        if isinstance(expected, str) and isinstance(actual, str):
            return actual.lower() == expected.lower()
        return actual == expected
    if op in ("!=", "<>"):
        return actual != expected
    try:
        a = float(actual)
        e = float(expected)
    except (TypeError, ValueError):
        return False
    if op == ">":
        return a > e
    if op == ">=":
        return a >= e
    if op == "<":
        return a < e
    if op == "<=":
        return a <= e
    return False


def evaluate_ast(node: ASTNode, context: dict[str, Any]) -> bool:
    if isinstance(node, BinaryOp):
        if node.op == "AND":
            return evaluate_ast(node.left, context) and evaluate_ast(node.right, context)
        if node.op == "OR":
            return evaluate_ast(node.left, context) or evaluate_ast(node.right, context)
    if isinstance(node, UnaryOp):
        if node.op == "NOT":
            return not evaluate_ast(node.operand, context)
    if isinstance(node, Comparison):
        actual = context.get(node.field)
        if actual is None:
            return False
        return _compare(actual, node.operator, node.value)
    if isinstance(node, Literal):
        return bool(node.value)
    return False


def evaluate_policy(expression: str, context: dict[str, Any]) -> bool:
    """Evaluate a policy expression against a context dict."""
    result = parse_policy(expression)
    return evaluate_ast(result.ast, context)


@dataclass
class PolicyRuleSpec:
    name: str
    expression: str
    action: str


class PolicyDSLEngine:
    """Evaluate multiple DSL rules and collect matching actions."""

    def __init__(self, rules: list[PolicyRuleSpec] | None = None) -> None:
        self.rules = rules or []
        self._cache: dict[str, ParseResult] = {}

    def _get_ast(self, expression: str) -> ParseResult:
        if expression not in self._cache:
            self._cache[expression] = parse_policy(expression)
        return self._cache[expression]

    def evaluate(self, context: dict[str, Any]) -> list[str]:
        actions: list[str] = []
        for rule in self.rules:
            if evaluate_ast(self._get_ast(rule.expression).ast, context):
                actions.append(rule.action)
        return actions

    def explain(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        explanations: list[dict[str, Any]] = []
        for rule in self.rules:
            matched = evaluate_ast(self._get_ast(rule.expression).ast, context)
            explanations.append({"name": rule.name, "expression": rule.expression, "matched": matched, "action": rule.action})
        return explanations


def validate_expression(expression: str) -> list[str]:
    """Return parse errors for an expression, empty if valid."""
    try:
        parse_policy(expression)
        return []
    except PolicyDSLError as exc:
        return [str(exc)]
