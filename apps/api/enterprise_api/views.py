from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET"])
def program(request: Request):
    data = get_container().enterprise.program()
    return envelope(data)


@api_view(["GET"])
def budget(request: Request):
    data = get_container().enterprise.budget()
    return envelope(data)


@api_view(["GET"])
def board_pack(request: Request):
    data = get_container().enterprise.board_pack()
    return envelope(data)


@api_view(["GET"])
def compliance(request: Request):
    data = get_container().enterprise.compliance()
    return envelope(data)


@api_view(["GET"])
def incidents(request: Request):
    data = get_container().enterprise.incidents()
    return envelope(data)
