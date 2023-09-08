from django.urls import path

from concurrency_api import views

urlpatterns = [
    path("concurrency/batch-score", views.batch_score, name="concurrency-batch-score"),
    path("concurrency/ingest", views.concurrency_ingest, name="concurrency-ingest"),
]
