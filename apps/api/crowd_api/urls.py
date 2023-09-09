from django.urls import path

from crowd_api import views

urlpatterns = [
    path("sets/<str:set_id>/narrative/arc", views.narrative_arc, name="narrative-arc"),
    path("sets/<str:set_id>/narrative/web", views.narrative_web, name="narrative-web"),
    path("themes/clusters", views.theme_clusters, name="theme-clusters"),
]
