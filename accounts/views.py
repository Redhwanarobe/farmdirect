"""Views for registering, logging in and logging out."""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm, VerifyCodeForm
from .services import (
    check_reverification,
    home_url_for,
    needs_reverification,
    start_reverification,
)


def register(request):
    """Show the sign-up form and create an account when it is valid."""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created. Welcome to FarmDirect!")
            return redirect(home_url_for(user))
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """Log the user in, or ask for a code if they were away for a year."""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            if needs_reverification(user):
                start_reverification(request.session, user)
                messages.info(
                    request,
                    "You have not logged in for over a year. "
                    "We sent a 6-digit code to your phone or email.",
                )
                return redirect("accounts:verify")
            login(request, user)
            messages.success(request, "Welcome back!")
            return redirect(home_url_for(user))
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def verify_view(request):
    """Check the 6-digit code and finish the login."""
    if "verify_user_id" not in request.session:
        return redirect("accounts:login")
    if request.method == "POST":
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            user, error = check_reverification(
                request.session, form.cleaned_data["code"]
            )
            if user is not None:
                login(request, user)
                messages.success(request, "Account verified. Welcome back!")
                return redirect(home_url_for(user))
            form.add_error("code", error)
    else:
        form = VerifyCodeForm()
    return render(request, "accounts/verify.html", {"form": form})


def logout_view(request):
    """Log the user out. Only a POST request logs out, for safety."""
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have logged out.")
    return redirect("core:home")
