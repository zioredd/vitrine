from django.urls import path

from parser_api import views

urlpatterns = [
    path("parser/tokenize", views.tokenize, name="parser-tokenize"),
    path("parser/parse", views.parse, name="parser-parse"),
    path("parser/compile", views.compile_query, name="parser-compile"),
]
