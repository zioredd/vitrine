from django.urls import path

from editorial_api import views

urlpatterns = [
    path("risks", views.risks, name="risks"),
    path("publication-windows", views.publication_windows, name="publication-windows"),
    path("editorial-signals", views.editorial_signals, name="editorial-signals"),
]
