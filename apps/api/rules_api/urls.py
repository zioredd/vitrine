from django.urls import path

from rules_api import views

urlpatterns = [
    path("rules/report", views.rules_report, name="rules-report"),
]
