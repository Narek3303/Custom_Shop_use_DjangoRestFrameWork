from django.db import models
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from coupon.models import Coupon
from shop.models import Product, Size, Color


User = settings.AUTH_USER_MODEL

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('closed', 'Closed')], default='open')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Cart for {self.user} - Status: {self.status}"

    def add_item(self, product, quantity=1):
        # Add or update an item in the cart
        cart_item, created = CartItem.objects.get_or_create(cart=self, product=product)
        cart_item.quantity += quantity
        cart_item.save()
        self.update_total_price()

    def remove_item(self, product, size=None, color=None):
        """
        Հեռացնում է ապրանքը զամբյուղից։ Եթե տրամադրվում է size կամ color, ապա այն հաշվի է առնում։
        """
        try:
            if size and color:
                cart_item = CartItem.objects.get(cart=self, product=product, size=size, color=color)
            else:
                cart_item = CartItem.objects.get(cart=self, product=product)

            cart_item.delete()
            self.update_total_price()
        except CartItem.DoesNotExist:
            pass

    def update_total_price(self):
        self.total_price = sum(item.total_price for item in self.items.all())
        self.save()

    def close(self):
        self.status = 'closed'
        self.save()

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def clear_cart(self):
        self.items.all().delete()
        self.update_total_price()

    def is_empty(self):
        return self.item_count == 0

    def add_product_to_cart(user, product, quantity=1):
        cart = Cart.objects.get_or_create_cart(user)
        cart.add_item(product, quantity)
        return cart

    def remove_product_from_cart(user, product):
        cart = Cart.objects.get_or_create_cart(user)
        cart.remove_item(product)
        return cart

    def close_cart(user):
        cart = Cart.objects.get_or_create_cart(user)
        if not cart.is_empty():
            cart.close()
        return cart



    # def apply_coupon(self, code):
    #     """
    #     Apply a coupon if valid, calculate discount, and disable it after use if it's one-time use.
    #     """
    #     try:
    #         coupon = Coupon.objects.get(code=code)
    #         if coupon.is_valid():
    #             self.coupon = coupon
    #             self.discount = self.get_total_price() * (coupon.discount / 100)
    #             self.session['coupon_code'] = coupon.code
    #
    #             if coupon.is_one_time_use:
    #                 coupon.is_used = True
    #                 coupon.save()
    #         else:
    #             from decimal import Decimal
    #             self.discount = Decimal(0)
    #             self.session.pop('coupon_code', None)
    #     except Coupon.DoesNotExist:
    #         self.discount = Decimal(0)
    #         self.session.pop('coupon_code', None)
    #
    #     self.save()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('shop.Product', on_delete=models.CASCADE)
    size = models.ForeignKey(Size, null=True, blank=True, on_delete=models.SET_NULL)  # Ավելացրինք չափս
    color = models.ForeignKey(Color, null=True, blank=True, on_delete=models.SET_NULL)  # Ավելացրինք գույն
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    def update_quantity(self, quantity):
        self.quantity = quantity
        self.save()


    def get_product_image(self):
        """Վերադարձնում է ապրանքի առաջին նկարը, եթե կա"""
        first_image = self.product.image.first()  # ստանում ենք առաջին նկարը
        return first_image.image.url if first_image else None  # վերադարձնում ենք URL-ը, եթե նկար կա






class CartManager(models.Manager):
    def get_or_create_cart(self, user):
        cart, created = self.get_or_create(user=user, status='open')
        return cart
