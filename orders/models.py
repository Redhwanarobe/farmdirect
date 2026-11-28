
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator


# ==========================
# SHOPPING CART
# ==========================

class Cart(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart - {self.user.username}"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def total_price(self):
        return sum(
            (item.subtotal for item in self.items.all()),
            start=0
        )


# ==========================
# CART ITEMS
# ==========================

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        "farms.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0.01)]
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_product_per_cart"
            )
        ]

    def __str__(self):
        product_name = self.product.name if self.product else "No product"
        return f"{product_name} - {self.quantity}"

    @property
    def subtotal(self):
        if self.product is None:
            return 0

        return self.product.price * self.quantity


# ==========================
# CUSTOMER ORDERS
# ==========================

class Order(models.Model):

    PAYMENT_METHODS = [
        ("bkash", "bKash"),
        ("nagad", "Nagad"),
        ("card", "Card"),
        ("cod", "Cash on Delivery"),
    ]

    ORDER_STATUSES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUSES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    delivery_address = models.TextField()

    city = models.CharField(
        max_length=100
    )

    phone = models.CharField(
        max_length=20
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default="pending"
    )

    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUSES,
        default="pending"
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


# ==========================
# ORDER ITEMS
# ==========================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        "farms.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    product_name = models.CharField(
        max_length=200
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.product_name} - Order #{self.order.id}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
