"""Pages where a farmer manages their own products."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductForm
from .models import Product
from .services import get_own_farm


@login_required
def dashboard(request):
    """Show the farmer's farm and all of its products."""
    farm = get_own_farm(request.user)
    products = farm.products.order_by("name")
    context = {"farm": farm, "products": products}
    return render(request, "farms/dashboard.html", context)


@login_required
def product_add(request):
    """Let the farmer add a new product to their farm."""
    farm = get_own_farm(request.user)
    form = ProductForm(request.POST or None)
    if form.is_valid():
        product = form.save(commit=False)
        product.farm = farm
        product.save()
        messages.success(request, f"{product.name} was added.")
        return redirect("farms:dashboard")
    context = {"form": form, "title": "Add product"}
    return render(request, "farms/product_form.html", context)


@login_required
def product_edit(request, pk):
    """Let the farmer change one of their own products."""
    farm = get_own_farm(request.user)
    product = get_object_or_404(Product, pk=pk, farm=farm)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, f"{product.name} was updated.")
        return redirect("farms:dashboard")
    context = {"form": form, "title": f"Edit {product.name}"}
    return render(request, "farms/product_form.html", context)
