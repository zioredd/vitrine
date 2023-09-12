from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET"])
def risks(request: Request):
    data = get_container().editorial.risks()
    return envelope(data)


@api_view(["GET"])
def publication_windows(request: Request):
    data = get_container().editorial.publication_windows()
    return envelope(data)


@api_view(["GET"])
def editorial_signals(request: Request):
    data = get_container().editorial.signals()
    return envelope(data)
