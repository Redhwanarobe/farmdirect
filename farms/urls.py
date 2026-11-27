"""URLs for the farmer dashboard."""

from django.urls import path

from . import views

app_name = "farms"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("product/add/", views.product_add, name="product_add"),
    path("product/<int:pk>/edit/", views.product_edit, name="product_edit"),
]
