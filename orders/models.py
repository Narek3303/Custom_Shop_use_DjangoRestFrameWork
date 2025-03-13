from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from coupons.models import Coupon
from shop.models import Product  # Assuming this model is in your shop app


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = "Pending", _("Pending")
        PROCESSING = "Processing", _("Processing")
        SHIPPED = "Shipped", _("Shipped")
        DELIVERED = "Delivered", _("Delivered")
        CANCELED = "Canceled", _("Canceled")

    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    email = models.EmailField(_('e-mail'))
    address = models.CharField(_('address'), max_length=250)
    postal_code = models.CharField(_('postal code'), max_length=20)
    city = models.CharField(_('city'), max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    stripe_id = models.CharField(max_length=250, blank=True)
    coupon = models.ForeignKey(
        Coupon,
        related_name='orders',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    discount = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f'Order {self.id} - {self.first_name} {self.last_name} ({self.status})'

    def get_total_cost_before_discount(self):
        """Returns the total cost before any discount is applied."""
        return sum(item.get_cost() for item in self.items.all())

    def get_total_quantity(self):
        """Returns the total quantity of items in the order."""
        return sum(item.quantity for item in self.items.all())

    def get_discount(self):
        """Calculates the discount based on the total cost."""
        total_cost = self.get_total_cost_before_discount()
        if self.discount:
            return total_cost * (self.discount / Decimal(100))
        return Decimal(0)

    def get_total_cost_after_discount(self):
        """Returns the total cost after applying the discount."""
        return self.get_total_cost_before_discount() - self.get_discount()

    def get_shipping_cost(self):
        """Calculates the shipping cost based on the total order amount."""
        total = self.get_total_cost_after_discount()
        return Decimal(0) if total > 100 else Decimal(5)  # Free shipping for orders > $100

    def get_vat(self, vat_rate=20):
        """Calculates VAT (default 20%) on the order."""
        return self.get_total_cost_after_discount() * (Decimal(vat_rate) / Decimal(100))

    def get_final_total(self):
        """Returns the final total cost including VAT and shipping."""
        return self.get_total_cost_after_discount() + self.get_shipping_cost() + self.get_vat()

    @property
    def full_address(self):
        """Returns a formatted full address."""
        return f"{self.address}, {self.city}, {self.postal_code}"





class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'Order Item {self.id} - {self.product.title}'

    def get_cost(self):
        """Returns the cost for this order item (price * quantity)."""
        return self.price * self.quantity

    def get_discounted_price(self):
        """Returns the price after applying product discount."""
        if self.product.discount_percent:
            discount_rate = Decimal(self.product.discount_percent) / Decimal(100)
            return self.price * (Decimal(1) - discount_rate)
        return self.price

    def get_total_cost(self):
        """Returns the total cost of this order item after applying product discount."""
        return self.get_discounted_price() * self.quantity

    @property
    def total_cost(self):
        """Returns the total cost (for templates)."""
        return self.get_total_cost()
