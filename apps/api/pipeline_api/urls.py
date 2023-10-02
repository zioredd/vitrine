from django.urls import path

from pipeline_api import views

urlpatterns = [
    path("pipeline/run", views.pipeline_run, name="pipeline-run"),
]
