"""Forms that farmers use to manage their products."""

from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    """Add or edit one product of the farmer's farm."""

    class Meta:
        model = Product
        fields = ["name", "category", "unit", "price", "stock", "is_active"]

    def __init__(self, *args, **kwargs):
        """Give every input a Bootstrap style."""
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "is_active":
                field.widget.attrs["class"] = "form-check-input"
            elif name == "unit":
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean_price(self):
        """Price must be more than 0 Taka."""
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be more than 0 Taka.")
        return price

    def clean_stock(self):
        """Stock can be 0 but never negative."""
        stock = self.cleaned_data["stock"]
        if stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock
