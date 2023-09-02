from django.urls import path

from ai_api import views

urlpatterns = [
    path("ai/recommend", views.recommend, name="ai-recommend"),
    path("ai/similar", views.similar, name="ai-similar"),
]
