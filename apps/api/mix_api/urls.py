from django.urls import path

from mix_api import views

urlpatterns = [
    path("sets/<str:set_id>/craft/pacing", views.craft_pacing, name="craft-pacing"),
    path("sets/<str:set_id>/craft/dialogue", views.craft_dialogue, name="craft-dialogue"),
]
