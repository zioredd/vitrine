from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["POST"])
def rebalance_route(request: Request):
    graph = request.data.get("graph", request.data)
    source = request.data.get("source")
    target = request.data.get("target")
    data = get_container().rebalance.route(graph, source=source, target=target)
    return envelope(data)
