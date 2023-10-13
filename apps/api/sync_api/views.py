from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["POST"])
def reconcile(request: Request):
    remote = request.data.get("remote", request.data)
    data = get_container().sync.reconcile(remote)
    return envelope(data)
