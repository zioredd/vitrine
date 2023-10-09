from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET"])
def rules_report(request: Request):
    data = get_container().rules.run_report()
    return envelope(data)
