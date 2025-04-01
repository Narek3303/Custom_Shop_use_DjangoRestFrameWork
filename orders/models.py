import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils.timezone import now
from paypal.standard.ipn.models import PayPalIPN
from shop.models import Product  # Adjust import as per your project structure
from django.core.exceptions import ValidationError
from django.db import transaction


class OrderStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    SHIPPED = "shipped", _("Shipped")
    DELIVERED = "delivered", _("Delivered")
    CANCELED = "canceled", _("Canceled")


class Order(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
    )

    # Այլ դաշտեր...
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='card'
    )

    order_number = models.CharField(
        max_length=20, unique=True, editable=False, db_index=True
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    status = models.CharField(
        max_length=15, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    tax = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    shipping_method = models.ForeignKey(
        'ShippingMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Shipping Method")
    )
    shipping_cost = models.DecimalField(
        _("Shipping Cost"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    tracking_number = models.CharField(
        _("Tracking Number"),
        max_length=100,
        blank=True,
        null=True
    )
    shipping_status = models.CharField(
        _("Shipping Status"),
        max_length=20,
        choices=[
            ('processing', _('Processing')),
            ('shipped', _('Shipped')),
            ('in_transit', _('In Transit')),
            ('delivered', _('Delivered')),
            ('cancelled', _('Cancelled'))
        ],
        default='processing'
    )
    shipped_at = models.DateTimeField(
        _("Shipped at"),
        blank=True,
        null=True
    )
    delivered_at = models.DateTimeField(
        _("Delivered at"),
        blank=True,
        null=True
    )



    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Override save method to generate order number and calculate total"""
        if not self.order_number:
            self.order_number = self.generate_order_number()
        self.total = self.calculate_total()

        # Validate that the total is not negative
        if self.total < 0:
            raise ValidationError("Total amount cannot be negative.")

        # Ensure atomic transaction to avoid issues with concurrent saves
        with transaction.atomic():
            super().save(*args, **kwargs)

    def generate_order_number(self):
        """Generate a unique order number."""
        return f"ORD-{uuid.uuid4().hex[:10].upper()}"

    def calculate_total(self):
        """Calculate the total cost including shipping"""
        return max(self.subtotal - self.discount + self.tax + self.shipping_cost, 0)

    def __str__(self):
        return f"Order {self.order_number} - {self.get_status_display()}"

    def send_confirmation_email(self):
        """Send order confirmation email (to be implemented)."""
        # Use Django's email backend for sending order confirmations.
        pass

    def clean(self):
        """Perform custom validation for the order."""
        if self.subtotal < 0:
            raise ValidationError({'subtotal': _("Subtotal cannot be negative.")})
        if self.discount < 0:
            raise ValidationError({'discount': _("Discount cannot be negative.")})
        if self.tax < 0:
            raise ValidationError({'tax': _("Tax cannot be negative.")})
        if not self.email:
            raise ValidationError({'email': _("Email address is required.")})
        if not self.address:
            raise ValidationError({'address': _("Shipping address is required.")})


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name=_("Order")
    )
    product = models.ForeignKey(
        'shop.Product',
        on_delete=models.PROTECT,
        verbose_name=_("Product")
    )
    quantity = models.PositiveIntegerField(
        _("Quantity"),
        default=1,
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        _("Price"),
        max_digits=10,
        decimal_places=2
    )
    weight = models.DecimalField(
        _("Weight (kg)"),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    def save(self, *args, **kwargs):
        """Auto-set price and weight from product if not set"""
        if not self.price or not self.weight:
            product = self.product
            if not self.price:
                self.price = product.price
            if not self.weight:
                self.weight = product.weight
        super().save(*args, **kwargs)

    def get_total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order: {self.order.order_number})"



class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_("Order")
    )
    status = models.CharField(
        _("Status"),
        max_length=50
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Changed By")
    )
    changed_at = models.DateTimeField(
        _("Changed At"),
        auto_now_add=True
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("Order Status History")
        verbose_name_plural = _("Order Status Histories")
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.status} at {self.changed_at}"



class ShippingMethod(models.Model):
    name = models.CharField(
        _("Name"),
        max_length=100
    )
    carrier = models.CharField(
        _("Carrier"),
        max_length=100,
        choices=[
            ('dhl', 'DHL'),
            ('fedex', 'FedEx'),
            ('ups', 'UPS'),
            ('local', _('Local Delivery')),
            ('pickup', _('Store Pickup'))
        ]
    )
    price = models.DecimalField(
        _("Price"),
        max_digits=10,
        decimal_places=2
    )
    estimated_delivery = models.CharField(
        _("Estimated Delivery"),
        max_length=100
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True
    )
    description = models.TextField(
        _("Description"),
        blank=True
    )

    class Meta:
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")

    def __str__(self):
        return f"{self.carrier.upper()} - {self.name}"



class ShippingAddress(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='shipping_address',
        verbose_name=_("Order")
    )
    country = models.CharField(
        _("Country"),
        max_length=100
    )
    city = models.CharField(
        _("City"),
        max_length=100
    )
    address_line1 = models.CharField(
        _("Address Line 1"),
        max_length=255
    )
    address_line2 = models.CharField(
        _("Address Line 2"),
        max_length=255,
        blank=True,
        null=True
    )
    postal_code = models.CharField(
        _("Postal Code"),
        max_length=20
    )
    phone = models.CharField(
        _("Phone"),
        max_length=20
    )
    notes = models.TextField(
        _("Delivery Notes"),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("Shipping Address")
        verbose_name_plural = _("Shipping Addresses")

    def __str__(self):
        return f"{self.city}, {self.address_line1} (Order: {self.order.order_number})"




class Shipping(models.Model):
    """
    Առաքման գրանցման մոդել
    """
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='shipping'
    )
    shipping_method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.SET_NULL,
        null=True
    )
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('in_transit', 'In Transit'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled')
        ],
        default='processing'
    )
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()}"


class Invoice(models.Model):
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='invoice')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number} for Order {self.order.id}"


