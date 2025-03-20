from django.contrib import admin
from .models import Cart, CartItem
from shop.models import Product

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1  # Number of empty cart items to show by default in the inline form

class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'updated_at', 'total_price', 'item_count')
    search_fields = ('user__username',)
    list_filter = ('status',)
    inlines = [CartItemInline]

    def item_count(self, obj):
        return obj.item_count
    item_count.admin_order_field = 'item_count'  # Allow sorting by item_count

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_as_closed.short_description = "Change status to closed"

    def clear_cart(self, request, queryset):
        for cart in queryset:
            cart.clear_cart()
    clear_cart.short_description = "Clear all items in selected carts"

    actions = ['mark_as_closed', 'clear_cart']

admin.site.register(Cart, CartAdmin)

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'price', 'total_price', 'cart')
    search_fields = ('product__name', 'cart__user__username')
    list_filter = ('cart__status',)

admin.site.register(CartItem, CartItemAdmin)
