"""URLs for restaurant bulk orders."""

from django.urls import path

from . import views

app_name = "bulk"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("credit/", views.credit_request, name="credit_request"),
    path("order/", views.place_order, name="place_order"),
    path("invoice/<int:pk>/pay/", views.pay, name="pay"),
]
