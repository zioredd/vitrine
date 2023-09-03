from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET"])
def weave_list(request: Request):
    data = get_container().catalog.list_exhibitions()
    return envelope(data)


@api_view(["GET"])
def set_detail(request: Request, set_id: str | None = None, exhibition_id: str | None = None):
    entity_id = set_id or exhibition_id
    data = get_container().catalog.get_exhibition(entity_id)
    return envelope(data)


@api_view(["GET"])
def tags(request: Request):
    data = get_container().catalog.list_tags()
    return envelope(data)


@api_view(["GET"])
def format_spectrum(request: Request):
    data = get_container().catalog.format_spectrum()
    return envelope(data)
