from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET", "POST"])
def batch_score(request: Request):
    ids = request.data.get("ids", []) if request.method == "POST" else request.query_params.getlist("ids")
    data = get_container().worker.batch_score(ids)
    return envelope(data)


@api_view(["GET", "POST"])
def concurrency_ingest(request: Request):
    payload = request.data if request.method == "POST" else dict(request.query_params)
    data = get_container().worker.ingest(payload)
    return envelope(data)
