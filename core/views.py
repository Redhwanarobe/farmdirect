
"""Views for shared pages such as the home page."""

from django.shortcuts import render
from farms.models import Product


def home(request):
    """Show the home page with available farm products."""

    products = Product.objects.filter(
        is_active=True,
        farm__is_active=True,
        stock__gt=0
    ).select_related("farm")

    return render(
        request,
        "core/home.html",
        {"products": products}
    )
