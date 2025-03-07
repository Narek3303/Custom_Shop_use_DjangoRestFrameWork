from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from coupons.models import Coupon
from shop.models import Product  # Assuming this model is present in your shop app


class Order(models.Model):
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

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f'Order {self.id} - {self.first_name} {self.last_name}'

    def get_total_cost_before_discount(self):
        """Returns the total cost before any discount."""
        return sum(item.get_cost() for item in self.items.all())

    def get_discount(self):
        """Calculates the discount based on total cost."""
        total_cost = self.get_total_cost_before_discount()
        if self.discount:
            return total_cost * (self.discount / Decimal(100))
        return Decimal(0)

    def get_total_cost(self):
        """Returns the total cost after applying the discount."""
        total_cost = self.get_total_cost_before_discount()
        return total_cost - self.get_discount()

    def get_stripe_url(self):
        """Returns the Stripe payment link for the order."""
        if not self.stripe_id:
            return ''
        path = '/test/' if '_test_' in settings.STRIPE_SECRET_KEY else '/'
        return f'https://dashboard.stripe.com{path}payments/{self.stripe_id}'

    @property
    def full_address(self):
        """Returns a formatted string with full address details."""
        return f"{self.address}, {self.city}, {self.postal_code}"



class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,  # Assuming 'Product' model is in your 'shop' app
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

    @property
    def total_cost(self):
        """Returns the total cost of this order item, including potential discounts on the product."""
        if self.product.discount_percent:
            discount_rate = Decimal(self.product.discount_percent) / Decimal(100)
            return self.price * (Decimal(1) - discount_rate) * self.quantity
        return self.get_cost()