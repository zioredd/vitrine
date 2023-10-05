from django.urls import path

from queue_api import views

urlpatterns = [
    path("queue/jobs", views.jobs, name="queue-jobs"),
    path("schedule", views.schedule, name="queue-schedule"),
    path("queue/dead-letter", views.dead_letter, name="queue-dead-letter"),
    path("queue/replay", views.replay, name="queue-replay"),
]
