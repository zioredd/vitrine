from rest_framework.decorators import api_view
from rest_framework.request import Request

from common.responses import envelope
from services.container import get_container


@api_view(["GET"])
def jobs(request: Request):
    data = get_container().queue.list_jobs()
    return envelope(data)


@api_view(["GET"])
def schedule(request: Request):
    data = get_container().scheduler.list_schedules()
    return envelope(data)


@api_view(["GET"])
def dead_letter(request: Request):
    data = get_container().retry.dead_letter_queue()
    return envelope(data)


@api_view(["POST"])
def replay(request: Request):
    job_id = request.data.get("job_id")
    data = get_container().retry.replay(job_id)
    return envelope(data)
