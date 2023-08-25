"""Root URL configuration for Vitrine API."""
from django.urls import include, path

urlpatterns = [
    path("v1/", include("catalog_api.urls")),
    path("v1/", include("mix_api.urls")),
    path("v1/", include("crowd_api.urls")),
    path("v1/", include("intelligence_api.urls")),
    path("v1/", include("editorial_api.urls")),
    path("v1/", include("enterprise_api.urls")),
    path("v1/", include("graph_api.urls")),
    path("v1/", include("parser_api.urls")),
    path("v1/", include("pipeline_api.urls")),
    path("v1/", include("concurrency_api.urls")),
    path("v1/", include("queue_api.urls")),
    path("v1/", include("ingest_api.urls")),
    path("v1/", include("rules_api.urls")),
    path("v1/", include("sync_api.urls")),
    path("v1/", include("rebalance_api.urls")),
    path("v1/", include("ai_api.urls")),
]
