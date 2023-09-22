from django.urls import path

from ingest_api import views

urlpatterns = [
    path("ingest/snapshot", views.ingest_snapshot, name="ingest-snapshot"),
]
