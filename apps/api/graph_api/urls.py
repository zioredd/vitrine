from django.urls import path

from graph_api import views

urlpatterns = [
    path("graph/sets/<str:set_id>/path", views.graph_path, name="graph-path"),
    path("graph/sets/<str:set_id>/traverse", views.graph_traverse, name="graph-traverse"),
    path("graph/residency-tree", views.residency_tree, name="residency-tree"),
]
