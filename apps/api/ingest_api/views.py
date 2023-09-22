from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["POST"])
def ingest_snapshot(request: Request):
    snapshot = request.data.get("snapshot", request.data)
    data = get_container().ingest.ingest_snapshot(snapshot)
    return envelope(data)
