from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET"])
def graph_path(request: Request, set_id: str):
    target = request.query_params.get("target")
    data = get_container().graph.shortest_path(set_id, target)
    return envelope(data)


@api_view(["GET"])
def graph_traverse(request: Request, set_id: str):
    depth = int(request.query_params.get("depth", 3))
    data = get_container().graph.traverse(set_id, depth=depth)
    return envelope(data)


@api_view(["GET"])
def residency_tree(request: Request):
    data = get_container().graph.residency_tree()
    return envelope(data)
