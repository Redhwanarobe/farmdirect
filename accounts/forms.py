"""Forms for registering and logging in FarmDirect users."""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from .models import User
from .services import find_username, normalize_bd_phone

ALREADY_REGISTERED = "Email or mobile number already registered."
INVALID_LOGIN = "Invalid email, mobile number or password."


class RegisterForm(UserCreationForm):
    """Sign-up form: name, email or mobile number, role and password."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "email", "phone", "role")
        labels = {"first_name": "Full name", "phone": "Mobile number"}

    def clean_phone(self):
        """Check the mobile number and store it as +8801XXXXXXXXX."""
        raw = self.cleaned_data.get("phone")
        if not raw:
            return None
        phone = normalize_bd_phone(raw)
        if phone is None:
            raise forms.ValidationError("Enter a valid Bangladeshi mobile number.")
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(ALREADY_REGISTERED)
        return phone

    def clean_email(self):
        """Make sure no other account uses this email."""
        email = self.cleaned_data.get("email", "").lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(ALREADY_REGISTERED)
        return email

    def clean(self):
        """Require at least one of email or mobile number."""
        cleaned = super().clean()
        has_contact_error = self.has_error("email") or self.has_error("phone")
        if (
            not has_contact_error
            and not cleaned.get("email")
            and not cleaned.get("phone")
        ):
            raise forms.ValidationError("Enter an email or a mobile number.")
        return cleaned

    def save(self, commit=True):
        """Create the user, using the phone or email as the username."""
        user = super().save(commit=False)
        user.username = user.phone or user.email
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Log in with an email or Bangladeshi mobile number and a password."""

    identifier = forms.CharField(label="Email or mobile number")
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        """Check the details, but never say which part was wrong."""
        cleaned = super().clean()
        username = find_username(cleaned.get("identifier", ""))
        user = None
        if username:
            user = authenticate(username=username, password=cleaned.get("password"))
        if user is None:
            raise forms.ValidationError(INVALID_LOGIN)
        cleaned["user"] = user
        return cleaned


class VerifyCodeForm(forms.Form):
    """Ask for the 6-digit code sent to a user who was away for a year."""

    code = forms.CharField(label="6-digit code", max_length=6)
