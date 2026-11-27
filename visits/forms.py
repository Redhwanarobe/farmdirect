"""Forms for booking a farm visit and adding visit slots."""

from django import forms
from django.utils import timezone

from .models import VisitSlot


class BookingForm(forms.Form):
    """How many people the customer is bringing."""

    people = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class VisitSlotForm(forms.ModelForm):
    """Let a farmer add a new visit date and time."""

    class Meta:
        model = VisitSlot
        fields = ["starts_at", "price_per_person", "capacity"]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
        labels = {
            "starts_at": "Date and time",
            "price_per_person": "Price per person (Tk)",
            "capacity": "How many visitors",
        }

    def __init__(self, *args, **kwargs):
        """Give every input a Bootstrap style."""
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_starts_at(self):
        """The visit must be in the future."""
        starts_at = self.cleaned_data["starts_at"]
        if starts_at <= timezone.now():
            raise forms.ValidationError("Please choose a future date and time.")
        return starts_at

    def clean_price_per_person(self):
        """Price must be more than 0 Taka."""
        price = self.cleaned_data["price_per_person"]
        if price <= 0:
            raise forms.ValidationError("Price must be more than 0 Taka.")
        return price

    def clean_capacity(self):
        """At least one visitor must fit."""
        capacity = self.cleaned_data["capacity"]
        if capacity < 1:
            raise forms.ValidationError("At least 1 visitor is needed.")
        return capacity
