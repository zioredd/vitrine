from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET"])
def narrative_arc(request: Request, set_id: str):
    data = get_container().crowd.arc(set_id)
    return envelope(data)


@api_view(["GET"])
def narrative_web(request: Request, set_id: str):
    data = get_container().crowd.web(set_id)
    return envelope(data)


@api_view(["GET"])
def theme_clusters(request: Request):
    data = get_container().crowd.theme_clusters()
    return envelope(data)
