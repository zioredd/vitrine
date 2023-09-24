from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET"])
def intelligence_report(request: Request):
    data = get_container().intelligence.report()
    return envelope(data)


@api_view(["GET"])
def command_center(request: Request):
    data = get_container().intelligence.command_center()
    return envelope(data)


@api_view(["GET"])
def editorial_decision_report(request: Request):
    data = get_container().intelligence.editorial_decision_report()
    return envelope(data)
