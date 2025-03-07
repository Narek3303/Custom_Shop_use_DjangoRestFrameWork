import csv
import datetime

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem


def export_to_csv(modeladmin, request, queryset):
    """Export selected orders to CSV."""
    opts = modeladmin.model._meta
    content_disposition = f'attachment; filename={opts.verbose_name}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = content_disposition
    writer = csv.writer(response)
    fields = [
        field
        for field in opts.get_fields()
        if not field.many_to_many and not field.one_to_many
    ]
    writer.writerow([field.verbose_name for field in fields])

    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            elif isinstance(value, datetime.date):
                value = value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)
    return response


export_to_csv.short_description = _('Export to CSV')


class OrderItemInline(admin.TabularInline):
    """Inline to show the order items in the admin interface."""
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0  # No extra empty rows for a cleaner interface
    verbose_name = _('Order Item')
    verbose_name_plural = _('Order Items')


def order_payment(obj):
    """Display Stripe payment URL as a clickable link."""
    url = obj.get_stripe_url()
    if obj.stripe_id:
        return mark_safe(f'<a href="{url}" target="_blank">{obj.stripe_id}</a>')
    return _('No payment')


order_payment.short_description = _('Stripe payment')


def order_detail(obj):
    """Create a link to view the order details."""
    url = reverse('orders:admin_order_detail', args=[obj.id])
    return mark_safe(f'<a href="{url}">{_("View")}</a>')


def order_pdf(obj):
    """Create a link to download the invoice PDF."""
    url = reverse('orders:admin_order_pdf', args=[obj.id])
    return mark_safe(f'<a href="{url}" target="_blank">{_("Invoice")}</a>')


order_pdf.short_description = _('Invoice')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order Admin interface configuration."""

    # List display configuration
    list_display = [
        'id', 'first_name', 'last_name', 'email', 'address', 'postal_code',
        'city', 'paid', order_payment, 'created', 'updated', order_detail, order_pdf,
    ]
    list_filter = ['paid', 'created', 'updated']
    search_fields = ['first_name', 'last_name', 'email', 'address']
    date_hierarchy = 'created'
    ordering = ['-created']

    # Enable inlines for related order items
    inlines = [OrderItemInline]

    # Custom actions
    actions = [export_to_csv]

    # Customize the form for adding or editing an order
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'address', 'postal_code', 'city')
        }),
        (_('Payment Info'), {
            'fields': ('paid', 'stripe_id', 'coupon', 'discount')
        }),
        (_('Dates'), {
            'fields': ('created', 'updated')
        }),
    )
    readonly_fields = ['created', 'updated']

    # Add bulk update functionality for the admin interface
    def bulk_update_paid_status(self, request, queryset):
        """Bulk update paid status of selected orders."""
        updated_count = queryset.update(paid=True)
        self.message_user(request, _('%d orders have been marked as paid.') % updated_count)

    bulk_update_paid_status.short_description = _('Mark as Paid')

    # Add an option to bulk apply discount to selected orders
    def bulk_apply_discount(self, request, queryset):
        """Bulk apply a discount to selected orders."""
        discount_value = request.POST.get('discount_value', 0)
        if discount_value:
            updated_count = queryset.update(discount=discount_value)
            self.message_user(request, _('%d orders have been updated with a discount of %s%%.') % (updated_count, discount_value))

    bulk_apply_discount.short_description = _('Apply discount to selected orders')

    def get_actions(self, request):
        """Custom actions for bulk updates in the admin interface."""
        actions = super().get_actions(request)
        actions['bulk_update_paid_status'] = self.bulk_update_paid_status
        actions['bulk_apply_discount'] = self.bulk_apply_discount
        return actions