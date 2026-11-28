"""Forms for restaurant credit requests and bulk orders."""

from decimal import Decimal

from django import forms

from farms.models import Product

from .models import CreditAccount


class CreditRequestForm(forms.ModelForm):
    """Ask the admin for 30-day credit."""

    class Meta:
        model = CreditAccount
        fields = ["business_name", "trade_license"]
        labels = {"trade_license": "Trade licence number"}

    def __init__(self, *args, **kwargs):
        """Give every input a Bootstrap style."""
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class BulkOrderForm(forms.Form):
    """Choose a product and how much to buy (10 or more)."""

    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True, stock__gt=0).select_related(
            "farm"
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    quantity = forms.DecimalField(
        min_value=Decimal("10"),
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
        help_text="Minimum 10. You get 10% off the normal price.",
    )
