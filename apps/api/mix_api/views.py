from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET"])
def craft_pacing(request: Request, set_id: str):
    data = get_container().mix.pacing(set_id)
    return envelope(data)


@api_view(["GET"])
def craft_dialogue(request: Request, set_id: str):
    data = get_container().mix.dialogue(set_id)
    return envelope(data)
