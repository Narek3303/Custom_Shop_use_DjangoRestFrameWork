import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from shop.models import Product
from users.models import UserProfile





class OrderStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    SHIPPED = "shipped", _("Shipped")
    DELIVERED = "delivered", _("Delivered")
    CANCELLED = "cancelled", _("Cancelled")
    CONFIRMED = "confirmed", _("Confirmed")
    REFUNDED = "refunded", _("Refunded")


class Order(models.Model):
    PAYMENT_METHODS = (
        ('cash', _('Cash')),
        ('card', _('Credit Card')),
        ('paypal', _('PayPal')),
        ('stripe', _('Stripe')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders', null=True, blank=True)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.PROTECT, blank=True, related_name='orders', null=True)
    order_number = models.CharField(max_length=30, unique=True, editable=False, db_index=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()

    status = models.CharField(max_length=15, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=(
        ('webmoney', 'WebMoney'),
        ('card', 'Credit Card'),
        # ... այլ մեթոդներ ...
    ), default='card')


    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))


    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return f"Order {self.order_number} ({self.get_status_display()})"

    def generate_order_number(self):
        today_str = timezone.now().strftime("%Y%m%d")
        unique_part = uuid.uuid4().hex[:8].upper()
        return f"ORD-{today_str}-{unique_part}"

    def calculate_subtotal(self):
        """
        Հաշվարկում է բոլոր ապրանքների ընդհանուր արժեքը
        """
        if not self.pk:  # Եթե պատվերը դեռ պահպանված չէ
            return Decimal('0.00')

        from django.db.models import Sum, F
        result = self.items.aggregate(
            subtotal=Sum(F('price') * F('quantity')))
        return result['subtotal'] or Decimal('0.00')

    def calculate_total(self):
        """
        Հաշվարկում է վերջնական գումարը
        """
        subtotal = self.calculate_subtotal()
        discount = self.discount if self.discount is not None else Decimal('0.00')
        tax = self.tax if self.tax is not None else Decimal('0.00')
        shipping_cost = self.shipping_cost if self.shipping_cost is not None else Decimal('0.00')

        total = subtotal - discount + tax + shipping_cost
        return max(total, Decimal('0.00'))

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()

        self.subtotal = self.calculate_subtotal()
        self.total = self.calculate_total()

        self.full_clean()
        super().save(*args, **kwargs)

    def populate_from_cart(self, cart):
        """
        Populate order items from the provided cart instance.
        """
        if not cart.items.exists():
            raise ValidationError(_("Cart is empty. Cannot create order."))

        with transaction.atomic():
            self.items.all().delete()  # Clean existing items if needed

            for cart_item in cart.items.select_related("product"):
                OrderItem.objects.create(
                    order=self,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    weight=cart_item.product.weight or Decimal('0.00'),
                    size=cart_item.size,
                    color=cart_item.color
                )
            self.save(update_fields=["subtotal", "total"])

    def mark_as_paid(self):
        self.is_paid = True
        self.save(update_fields=["is_paid"])

    def mark_as_shipped(self, tracking_number: str):
        self.status = OrderStatus.SHIPPED
        self.tracking_number = tracking_number
        self.shipped_at = timezone.now()
        self.save(update_fields=["status", "tracking_number", "shipped_at"])

    def mark_as_delivered(self):
        self.status = OrderStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=["status", "delivered_at"])

    def clean(self):
        errors = {}
        if not self.email or '@' not in self.email:
            errors['email'] = _("Enter a valid email address.")
        if not self.phone:
            errors['phone'] = _("Phone number is required.")
        if not self.address:
            errors['address'] = _("Shipping address is required.")
        if errors:
            raise ValidationError(errors)

    @property
    def status_display(self):
        """Համապատասխանում է API-ում օգտագործվող status_display-ին"""
        return self.get_status_display()

    def get_order_items_data(self):
        """Վերադարձնում է պատվերի ապրանքների տվյալները API-ի համար"""
        return [
            {
                "id": item.id,
                "product": item.product.id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price": str(item.price),
                "total_price": float(item.price * item.quantity),
                # ... այլ դաշտեր ...
            }
            for item in self.items.all()
        ]

    def currency_code(self, request):
        price_currency = getattr(request, 'currency_code')
        return price_currency

    def to_api_dict(self):
        """Վերադարձնում է պատվերի տվյալները API պատասխանի համար"""
        return {
            "id": self.id,
            "order_number": self.order_number,
            "status": self.status,
            "status_display": self.status_display,
            "total": float(self.total),
            "items": self.get_order_items_data(),
            # ... այլ դաշտեր ...
        }


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), editable=False)
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        ordering = ['-id']

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.order.order_number})"

    @property
    def total_price(self):
        return self.quantity * self.price

    def clean(self):
        if self.price != self.product.price:
            raise ValidationError(_("Order item price must match product price."))
        if self.weight != self.product.weight:
            raise ValidationError(_("Order item weight must match product weight."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def currency_code(self, request):
        price_currency = getattr(request, 'currency_code')
        return price_currency

