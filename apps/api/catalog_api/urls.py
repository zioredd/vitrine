from django.urls import path

from catalog_api import views

urlpatterns = [
    path("weave", views.weave_list, name="weave-list"),
    path("sets/<str:set_id>", views.set_detail, name="set-detail"),
    path("exhibitions/<str:exhibition_id>", views.set_detail, name="exhibition-detail"),
    path("tags", views.tags, name="tags"),
    path("format-spectrum", views.format_spectrum, name="format-spectrum"),
]
