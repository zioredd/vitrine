from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET", "POST"])
def recommend(request: Request):
    set_id = request.data.get("set_id") if request.method == "POST" else request.query_params.get("set_id")
    data = get_container().ai.recommend(set_id)
    return envelope(data)


@api_view(["GET", "POST"])
def similar(request: Request):
    set_id = request.data.get("set_id") if request.method == "POST" else request.query_params.get("set_id")
    data = get_container().ai.similar(set_id)
    return envelope(data)
