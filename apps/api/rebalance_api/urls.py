from django.urls import path

from rebalance_api import views

urlpatterns = [
    path("rebalance/route", views.rebalance_route, name="rebalance-route"),
]
