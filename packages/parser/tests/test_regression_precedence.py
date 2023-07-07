"""Regression: AND binds tighter than OR."""

from vitrine_parser.query import compile_filter, parse_query


def test_or_binds_looser_than_and():
    ast = parse_query("a:1 OR b:2 AND c:3")
    compiled = compile_filter(ast)
    assert "or" in compiled
    assert "and" in compiled["or"][1]
