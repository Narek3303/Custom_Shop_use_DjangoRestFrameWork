from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem, OrderStatus
from django.utils.timezone import now
from django.db import transaction



class OrderItemInline(admin.TabularInline):
    """
    Inline admin for OrderItem, allowing order items to be edited inside an Order.
    """
    model = OrderItem
    extra = 1  # Allow adding new items
    readonly_fields = ("total_price",)

    def total_price(self, obj):
        # Ensure quantity and price are not None before multiplication
        if obj.quantity and obj.price:
            return obj.quantity * obj.price
        return 0  # Return 0 if either value is None

    total_price.short_description = "Total Price"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin panel for Order model with enhanced security, functionality, and readability.
    Ensures data integrity and provides a user-friendly experience for administrators.
    """
    list_display = (
        "order_number", "user", "email", "phone", "status",
        "subtotal", "discount", "tax", "total", "created_at", "updated_at"
    )
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "user__email", "phone")
    readonly_fields = ("order_number", "subtotal", "discount", "tax", "total", "created_at", "updated_at")
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        """
        Override save_model to ensure total recalculation and validate input before saving the order.
        """
        try:
            # Validate order fields before recalculating total
            if obj.subtotal < 0:
                raise ValidationError(_("Subtotal cannot be negative."))
            if obj.discount < 0:
                raise ValidationError(_("Discount cannot be negative."))
            if obj.tax < 0:
                raise ValidationError(_("Tax cannot be negative."))

            obj.total = obj.calculate_total()

            if obj.total < 0:
                raise ValidationError(_("Total amount cannot be negative."))

            # Optionally add a timestamp for logging purposes (e.g., to track last changes)
            obj.updated_at = now()

        except ValidationError as e:
            self.message_user(request, f"Error recalculating total: {e.message}", level="error")
            return

        # Only save if all validations passed
        obj.save()

    def get_readonly_fields(self, request, obj=None):
        """
        Dynamically set readonly fields based on the order status.
        If the order is shipped or delivered, make all fields readonly except the status.
        """
        readonly_fields = list(self.readonly_fields)

        if obj and obj.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            readonly_fields.extend(
                ["status", "user", "email", "phone", "address", "subtotal", "discount", "tax", "total"])

        return readonly_fields

    def has_change_permission(self, request, obj=None):
        """
        Prevent any changes to orders that are already shipped or delivered.
        """
        if obj and obj.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            return False  # No change permission for shipped or delivered orders
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of orders that are shipped or delivered.
        """
        if obj and obj.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            return False  # Prevent deletion for shipped or delivered orders
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        """
        Override the get_actions method to dynamically remove 'delete selected' action
        for orders that are shipped or delivered.
        """
        actions = super().get_actions(request)
        if request.user.is_superuser:
            return actions  # Admins have full access

        # Remove delete action for non-superusers if the order is shipped or delivered
        for order in self.get_queryset(request):
            if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                actions.pop('delete_selected', None)

        return actions


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Admin panel for OrderItem model with enhanced functionality, validation, security, and data integrity.
    """
    list_display = ("order", "product", "quantity", "price", "total_price", "product_stock")
    search_fields = ("order__order_number", "product__name")
    readonly_fields = ("total_price",)
    list_filter = ("order__status",)  # Added filter to sort by order status
    ordering = ("-order__created_at",)  # Default ordering by order creation date

    def total_price(self, obj):
        """
        Calculate total price for an order item: quantity * price.
        """
        return obj.quantity * obj.price

    total_price.short_description = _("Total Price")

    def product_stock(self, obj):
        """
        Display the current stock level for the product.
        """
        return obj.product.stock if obj.product else 0  # Assuming 'stock' field exists in the Product model

    product_stock.short_description = _("Product Stock")

    def save_model(self, request, obj, form, change):
        """
        Override save_model to include validation, price consistency, and atomic transaction for data integrity.
        """
        # Validate quantity and price
        if obj.quantity <= 0:
            raise ValidationError(_("Quantity must be greater than zero."))
        if obj.price < 0:
            raise ValidationError(_("Price cannot be negative."))

        # Ensure the product's price matches the price field in OrderItem
        if obj.product and obj.price != obj.product.price:
            raise ValidationError(
                _("Price does not match the current product price. Please update the product's price."))

        # Additional check for stock availability
        if obj.quantity > obj.product.stock:
            raise ValidationError(_("Insufficient stock for the requested quantity."))

        # Start a transaction to ensure data integrity
        with transaction.atomic():
            # Update product stock before saving order item
            if obj.product:
                obj.product.stock -= obj.quantity
                obj.product.save()

            super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        """
        Prevent changes to OrderItem if the parent order is already shipped or delivered.
        Also, prevent changes if the item quantity exceeds available stock.
        """
        if obj and obj.order.status in ["shipped", "delivered"]:
            self.message_user(request, _("Cannot modify items from shipped or delivered orders."), level="error")
            return False  # Prevent changes to shipped or delivered orders

        # Ensure no changes if quantity exceeds stock
        if obj and obj.quantity > obj.product.stock:
            self.message_user(request, _("Cannot update the item due to insufficient stock."), level="error")
            return False

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of OrderItem if the parent order is already shipped or delivered.
        """
        if obj and obj.order.status in ["shipped", "delivered"]:
            self.message_user(request, _("Cannot delete items from shipped or delivered orders."), level="error")
            return False  # Prevent deletion for shipped or delivered orders
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Override delete_queryset to handle item deletions safely by checking stock levels.
        """
        for order_item in queryset:
            if order_item.order.status in ["shipped", "delivered"]:
                self.message_user(request, _("Cannot delete items from shipped or delivered orders."), level="error")
            else:
                # Update product stock when deleting order items
                if order_item.product:
                    order_item.product.stock += order_item.quantity
                    order_item.product.save()

        # Proceed with deletion
        queryset.delete()

    def get_actions(self, request):
        """
        Override get_actions to add custom actions (if any) or limit actions based on conditions.
        """
        actions = super().get_actions(request)
        if request.user.is_superuser:
            # Example: Disable the delete action for superusers in specific cases
            actions = {key: value for key, value in actions.items() if key != 'delete_selected'}
        return actions
