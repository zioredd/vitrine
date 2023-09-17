from django.urls import path

from enterprise_api import views

urlpatterns = [
    path("enterprise/program", views.program, name="enterprise-program"),
    path("enterprise/budget", views.budget, name="enterprise-budget"),
    path("enterprise/board-pack", views.board_pack, name="enterprise-board-pack"),
    path("enterprise/compliance", views.compliance, name="enterprise-compliance"),
    path("enterprise/incidents", views.incidents, name="enterprise-incidents"),
]
