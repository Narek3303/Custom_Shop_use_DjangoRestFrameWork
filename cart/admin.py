from django.contrib import admin
from .models import Cart, CartItem
from django.utils.safestring import mark_safe


class CartItemInline(admin.TabularInline):
    """Inline for adding CartItems within the Cart admin page."""
    model = CartItem
    extra = 1  # Default number of extra forms to display


class CartAdmin(admin.ModelAdmin):
    """Admin interface for Cart model."""
    list_display = ['id', 'user', 'created_at', 'updated_at', 'total_price', 'total_items']
    list_filter = ['created_at', 'updated_at', 'user']
    search_fields = ['user__username', 'user__email']
    inlines = [CartItemInline]

    def total_price(self, obj):
        """Calculated field to show the total price of the cart."""
        return obj.total_price

    total_price.short_description = 'Total Price'

    def total_items(self, obj):
        """Calculated field to show the total number of items in the cart."""
        return obj.total_items

    total_items.short_description = 'Total Items'


class CartItemAdmin(admin.ModelAdmin):
    """Admin interface for CartItem model."""
    list_display = ['cart', 'product', 'quantity', 'price', 'total_price']
    list_filter = ['cart', 'product']
    search_fields = ['product__name', 'cart__user__username']

    def total_price(self, obj):
        """Calculated field to show the total price of the cart item."""
        return obj.total_price

    total_price.short_description = 'Total Price'


# Register the models with their corresponding admin configurations
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
