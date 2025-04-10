from django.contrib import admin
from django.utils.html import mark_safe
from .models import Category, Product, SubCategory, Image, Size, Color, Slider, Brand, \
                DiscountedShowModel, Wishlist, Review, Currency, SizePrice
from .forms import ImageAdminForm, ProductAdminForm


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'exchange_rate']



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}







@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'image']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(DiscountedShowModel)
class DiscountedShowAdmin(admin.ModelAdmin):
    list_display = ['image', 'min_discount', 'max_discount', 'available']
    list_editable = ['available']


from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse
from django import forms


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from .models import Product


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        'show_first_image',
        'name_with_link',
        'category',
        'brand',
        'price_display',
        'discount_display',
        'available',  # Added to make it editable
        'stock_status',
        'status_badge',
        'created_short',
        'action_buttons'
    )
    list_display_links = ('name_with_link',)
    list_filter = (
        ('category', admin.RelatedOnlyFieldListFilter),
        ('brand', admin.RelatedOnlyFieldListFilter),
        'status',
        'available',
        'created',
    )
    search_fields = (
        'name',
        'description',
        'tags__name',
        'article',
        'category__name',
        'brand__name'
    )
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('image', 'size', 'colors', 'related_products')  # Removed 'tags'
    list_editable = ('available',)  # Now valid since 'available' is in list_display
    list_per_page = 25
    ordering = ('-created',)
    readonly_fields = (
        'article',
        'created',
        'updated',
        'product_images_preview'
    )
    actions = ['make_available', 'make_unavailable', 'set_status_draft']
    save_on_top = True
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'article', 'category', 'brand', 'tags')  # Added tags here
        }),
        ('Pricing', {
            'fields': ('price', 'discount_percentage'),
            'classes': ('collapse',)
        }),
        ('Details', {
            'fields': ('description', 'size', 'colors'),
            'classes': ('collapse',)
        }),
        ('Inventory & Status', {
            'fields': ('available', 'status', 'related_products'),
        }),
        ('Media', {
            'fields': ('image', 'product_images_preview'),
        }),
        ('Metadata', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    # Custom display methods
    def show_first_image(self, obj):
        first_image = obj.image.first()
        if first_image:
            return mark_safe(
                f'<img src="{first_image.image.url}" width="50" height="50" '
                f'style="object-fit: cover; border-radius: 3px;" />'
            )
        return format_html(
            '<div style="width:50px; height:50px; background:#f5f5f5; '
            'display:flex; align-items:center; justify-content:center; '
            'border-radius:3px; color:#999;">No Image</div>'
        )

    show_first_image.short_description = 'Image'

    def name_with_link(self, obj):
        url = reverse('admin:shop_product_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.name)

    name_with_link.short_description = 'Name'
    name_with_link.admin_order_field = 'name'

    def price_display(self, obj):
        return f"${obj.price:.2f}"

    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'

    def discount_display(self, obj):
        if obj.discount_percentage:
            return f"{obj.discount_percentage}%"
        return "-"

    discount_display.short_description = 'Discount'
    discount_display.admin_order_field = 'discount_percentage'

    def final_price_display(self, obj):
        return f"${obj.get_final_price():.2f}"

    final_price_display.short_description = 'Final Price'

    def stock_status(self, obj):
        if obj.available:
            return format_html('<span style="color:green;">✓ In Stock</span>')
        return format_html('<span style="color:red;">✗ Out of Stock</span>')

    stock_status.short_description = 'Stock'

    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'published': '#28a745',
            'archived': '#dc3545',
        }
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; '
            'border-radius:10px; font-size:12px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def created_short(self, obj):
        return obj.created.strftime('%b %d, %Y')

    created_short.short_description = 'Created'
    created_short.admin_order_field = 'created'

    def product_images_preview(self, obj):
        images = obj.image.all()[:5]
        if not images:
            return "No images uploaded yet."

        previews = []
        for img in images:
            previews.append(
                f'<img src="{img.image.url}" width="80" height="80" '
                'style="object-fit: cover; margin-right: 5px; '
                'border: 1px solid #eee; border-radius: 3px;" />'
            )
        return mark_safe(''.join(previews))

    product_images_preview.short_description = 'Images Preview'

    def action_buttons(self, obj):
        return format_html(
            '<div class="action-buttons">'
            '<a class="button" href="{}" style="padding:2px 5px; '
            'background:#417690; color:white; border-radius:3px; '
            'margin-right:3px;">View</a>'
            '<a class="button" href="{}" style="padding:2px 5px; '
            'background:#28a745; color:white; border-radius:3px;">Edit</a>'
            '</div>',
            obj.get_absolute_url(),
            reverse('admin:shop_product_change', args=[obj.id])
        )

    action_buttons.short_description = 'Actions'
    action_buttons.allow_tags = True

    # Bulk action methods
    def make_available(self, request, queryset):
        updated = queryset.update(available=True)
        self.message_user(
            request,
            f"{updated} products were successfully marked as available."
        )

    make_available.short_description = "Mark selected products as available"

    def make_unavailable(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(
            request,
            f"{updated} products were successfully marked as unavailable."
        )

    make_unavailable.short_description = "Mark selected products as unavailable"

    def set_status_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(
            request,
            f"{updated} products were set to draft status."
        )

    set_status_draft.short_description = "Set status to draft"

    # Custom media for admin
    class Media:
        css = {
            'all': ('admin/css/product_admin.css',)
        }
        js = (
            'admin/js/product_admin.js',
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'brand'
        ).prefetch_related(
            'image', 'size', 'colors', 'tags'
        )

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview']
    readonly_fields = ('image_preview',)

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'notified']
    readonly_fields = ['price', 'final_price']




@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_code']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ('name',)}



class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'status', 'created_at')
    list_filter = ('status', 'product')
    search_fields = ('user__email', 'product__name', 'status')
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(status=Review.Status.APPROVED)
        self.message_user(request, "Selected reviews have been approved.")
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        queryset.update(status=Review.Status.REJECTED)
        self.message_user(request, "Selected reviews have been rejected.")
    reject_reviews.short_description = "Reject selected reviews"

admin.site.register(Review, ReviewAdmin)


@admin.register(SizePrice)
class SizePriceAdmin(admin.ModelAdmin):
    list_display = ['product', 'price', 'size']




# --------------------------------------------------------


