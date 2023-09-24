from django.urls import path

from intelligence_api import views

urlpatterns = [
    path("intelligence", views.intelligence_report, name="intelligence"),
    path("command-center", views.command_center, name="command-center"),
    path("editorial-decision-report", views.editorial_decision_report, name="editorial-decision-report"),
]
