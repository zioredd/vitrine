from django.urls import path

from sync_api import views

urlpatterns = [
    path("sync/reconcile", views.reconcile, name="sync-reconcile"),
]
