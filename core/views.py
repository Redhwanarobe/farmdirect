"""Views for shared pages such as the home page."""

from django.shortcuts import render


def home(request):
    """Show the FarmDirect home page."""
    return render(request, "core/home.html")
