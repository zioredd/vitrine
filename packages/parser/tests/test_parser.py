import pytest

from vitrine_parser.query import compile_filter, parse_query, tokenize, TokenKind


def test_tokenize_and_or_not():
    toks = tokenize('genre:"modern" AND score >= 70 OR NOT residency:"Tate"')
    kinds = [t.kind for t in toks if t.kind != TokenKind.EOF]
    assert TokenKind.AND in kinds
    assert TokenKind.OR in kinds
    assert TokenKind.NOT in kinds


def test_parse_simple_compare():
    ast = parse_query("vitrine_score >= 80")
    compiled = compile_filter(ast)
    assert compiled["field"] == "vitrine_score"
    assert compiled["op"] == ">="
    assert compiled["value"] == 80


def test_parse_match_colon():
    ast = parse_query('genre:"contemporary"')
    compiled = compile_filter(ast)
    assert compiled["op"] == "match"
    assert compiled["value"] == "contemporary"


def test_parse_and_precedence():
    ast = parse_query("a:1 AND b:2 OR c:3")
    compiled = compile_filter(ast)
    assert "or" in compiled
    assert len(compiled["or"]) == 2


def test_parse_not():
    ast = parse_query("NOT closed:true")
    compiled = compile_filter(ast)
    assert "not" in compiled


def test_parse_parens():
    ast = parse_query("(genre:modern AND score >= 50) OR curator:Smith")
    compiled = compile_filter(ast)
    assert "or" in compiled


def test_invalid_token_raises():
    with pytest.raises(SyntaxError):
        tokenize("score @ 5")
