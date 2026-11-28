"""URL configuration for the FarmDirect project."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Forgot password (Django's built-in, safe reset flow)
    path(
        "accounts/password-reset/",
        auth_views.PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "accounts/password-reset/sent/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("accounts/", include("accounts.urls")),
    path("farms/", include("farms.urls")),
    path("visits/", include("visits.urls")),
    path("orders/", include("orders.urls")),
    path("bulk/", include("bulk.urls")),
    path("recipes/", include("recipes.urls")),
    path("", include("core.urls")),
]
