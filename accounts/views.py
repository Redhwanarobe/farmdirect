"""Views for registering, logging in and logging out."""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm


def register(request):
    """Show the sign-up form and create an account when it is valid."""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created. Welcome to FarmDirect!")
            return redirect("core:home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """Show the login form and log the user in when the details are right."""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            messages.success(request, "Welcome back!")
            return redirect("core:home")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    """Log the user out. Only a POST request logs out, for safety."""
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have logged out.")
    return redirect("core:home")
