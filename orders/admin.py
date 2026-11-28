
from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "added_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "total_amount",
        "payment_method",
        "payment_status",
        "order_status",
        "created_at",
    )

    list_filter = (
        "payment_method",
        "payment_status",
        "order_status",
    )

    search_fields = (
        "user__username",
        "phone",
        "city",
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_name",
        "quantity",
        "unit_price",
    )
