from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["POST"])
def tokenize(request: Request):
    expression = request.data.get("expression", "")
    data = get_container().parser.tokenize(expression)
    return envelope(data)


@api_view(["POST"])
def parse(request: Request):
    expression = request.data.get("expression", "")
    data = get_container().parser.parse(expression)
    return envelope(data)


@api_view(["POST"])
def compile_query(request: Request):
    ast = request.data.get("ast") or request.data.get("expression", "")
    data = get_container().parser.compile(ast)
    return envelope(data)
