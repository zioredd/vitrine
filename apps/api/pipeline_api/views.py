from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["POST"])
def pipeline_run(request: Request):
    payload = request.data.get("payload", request.data)
    stages = request.data.get("stages", [])
    data = get_container().pipeline.run(stages=stages, payload=payload)
    return envelope(data)
