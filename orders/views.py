
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

from farms.models import Product
from .models import Cart, CartItem, Order, OrderItem


@login_required
def cart_view(request):
    if request.user.role != "customer":
        return HttpResponseForbidden("Only customers can access the shopping cart.")

    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, "orders/cart.html", {"cart": cart})


@login_required
@require_POST
def add_to_cart(request, product_id):
    if request.user.role != "customer":
        return HttpResponseForbidden("Only customers can add products to a cart.")

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
        farm__is_active=True
    )

    cart, created = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": 1}
    )

    if created:
        if product.stock < item.quantity:
            item.delete()
            messages.error(request, "Not enough stock available.")
            return redirect("orders:cart")
    else:
        if item.quantity + 1 > product.stock:
            messages.error(request, "Not enough stock available.")
            return redirect("orders:cart")

        item.quantity += 1
        item.save()

    messages.success(request, f"{product.name} added to your cart.")
    return redirect("orders:cart")


@login_required
@require_POST
def update_cart_item(request, item_id):
    if request.user.role != "customer":
        return HttpResponseForbidden("Only customers can update their cart.")

    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    try:
        quantity = Decimal(request.POST.get("quantity", ""))
    except (InvalidOperation, TypeError):
        messages.error(request, "Please enter a valid quantity.")
        return redirect("orders:cart")

    if not quantity.is_finite() or quantity <= 0:
        messages.error(request, "Quantity must be greater than zero.")
        return redirect("orders:cart")

    if item.product is None:
        messages.error(request, "This product is no longer available.")
        return redirect("orders:cart")

    if quantity > item.product.stock:
        messages.error(
            request,
            f"Only {item.product.stock} {item.product.unit} available."
        )
        return redirect("orders:cart")

    item.quantity = quantity
    item.save()

    messages.success(request, "Cart quantity updated successfully.")
    return redirect("orders:cart")


@login_required
@require_POST
def remove_cart_item(request, item_id):
    if request.user.role != "customer":
        return HttpResponseForbidden("Only customers can manage the shopping cart.")

    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    item.delete()
    messages.success(request, "Item removed from your cart.")

    return redirect("orders:cart")


@login_required
def checkout(request):
    if request.user.role != "customer":
        return HttpResponseForbidden("Only customers can checkout.")

    cart = get_object_or_404(Cart, user=request.user)

    cart_items = list(
        cart.items.select_related("product", "product__farm").all()
    )

    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect("orders:cart")

    if request.method == "POST":
        delivery_address = request.POST.get("delivery_address", "").strip()
        city = request.POST.get("city", "").strip()
        phone = request.POST.get("phone", "").strip()
        payment_method = request.POST.get("payment_method", "")

        valid_payment_methods = dict(Order.PAYMENT_METHODS)

        if not delivery_address or not city or not phone:
            messages.error(request, "Please complete all delivery information.")
            return redirect("orders:checkout")

        if payment_method not in valid_payment_methods:
            messages.error(request, "Please select a valid payment method.")
            return redirect("orders:checkout")

        try:
            with transaction.atomic():
                order_products = []
                total_amount = Decimal("0.00")

                for item in cart_items:
                    if item.product is None:
                        messages.error(request, "A product in your cart is unavailable.")
                        return redirect("orders:cart")

                    try:
                        product = Product.objects.select_for_update().get(
                            id=item.product_id
                        )
                    except Product.DoesNotExist:
                        messages.error(request, "A product in your cart no longer exists.")
                        return redirect("orders:cart")

                    if not product.is_active or not product.farm.is_active:
                        messages.error(request, f"{product.name} is no longer available.")
                        return redirect("orders:cart")

                    if item.quantity > product.stock:
                        messages.error(
                            request,
                            f"Only {product.stock} {product.unit} of {product.name} is available."
                        )
                        return redirect("orders:cart")

                    subtotal = product.price * item.quantity
                    total_amount += subtotal
                    order_products.append((item, product))

                order = Order.objects.create(
                    user=request.user,
                    delivery_address=delivery_address,
                    city=city,
                    phone=phone,
                    payment_method=payment_method,
                    payment_status="pending",
                    order_status="pending",
                    total_amount=total_amount
                )

                for item, product in order_products:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        quantity=item.quantity,
                        unit_price=product.price
                    )

                    product.stock -= item.quantity
                    product.save(update_fields=["stock"])

                cart.items.all().delete()

            messages.success(request, "Your order has been placed successfully!")
            return redirect("orders:order_success", order_id=order.id)

        except InvalidOperation:
            messages.error(request, "There was a problem calculating your order.")
            return redirect("orders:cart")

    return render(
        request,
        "orders/checkout.html",
        {"cart": cart, "cart_items": cart_items}
    )


@login_required
def order_success(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(request, "orders/order_success.html", {"order": order})


@login_required
def order_history(request):
    if request.user.role != "customer":
        return HttpResponseForbidden("Only customers can view order history.")

    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    return render(
        request,
        "orders/order_history.html",
        {"orders": orders}
    )


@login_required
def order_detail(request, order_id):
    if request.user.role != "customer":
        return HttpResponseForbidden("Only customers can view order details.")

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "orders/order_detail.html",
        {"order": order}
    )
