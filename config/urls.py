
"""URL configuration for the FarmDirect project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("farms/", include("farms.urls")),
    path("visits/", include("visits.urls")),
    path("orders/", include("orders.urls")),
    path("", include("core.urls")),
]
