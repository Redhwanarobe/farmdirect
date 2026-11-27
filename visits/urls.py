"""URLs for farm visit booking."""

from django.urls import path

from . import views

app_name = "visits"

urlpatterns = [
    path("", views.slot_list, name="slot_list"),
    path("<int:pk>/book/", views.book, name="book"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("farmer/", views.farmer_slots, name="farmer_slots"),
    path("farmer/add/", views.slot_add, name="slot_add"),
    path("farmer/<int:pk>/cancel/", views.slot_cancel, name="slot_cancel"),
]
