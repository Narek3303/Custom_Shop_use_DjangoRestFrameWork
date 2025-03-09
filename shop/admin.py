from django.contrib import admin
from django.utils.html import mark_safe
from .models import Category, Product, SubCategory, Image, Size, Color, Slider, Brand


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}




@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'image']
    prepopulated_fields = {'slug': ('name',)}




class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'brand', 'price', 'discount_percentage', 'available', 'status', 'created', 'updated', 'show_first_image')
    list_filter = ('category', 'brand', 'status', 'available')
    search_fields = ('name', 'description', 'tags__name')  # Allows searching by tags as well
    prepopulated_fields = {'slug': ('name',)}  # Auto-generate the slug from product name
    filter_horizontal = ('image', 'size', 'colors')  # ManyToMany fields displayed as a filter
    list_editable = ('available', 'status')  # Inline editing available/ status
    ordering = ('-created',)  # Ordering the products by creation date descending

    # Show final price calculation in list display
    def get_final_price_display(self, obj):
        return obj.get_final_price()
    get_final_price_display.short_description = 'Final Price'
    list_display += ('get_final_price_display',)

    # Optionally, you can also add inlines for categories or other related models
    # (e.g. if there are inline models like ProductImage or variants)
    def show_first_image(self, obj):
        # Գտնում ենք առաջին նկարը
        first_image = obj.image.all().first()

        # Եթե առաջին նկարը կա, ապա ցուցադրեք այն, եթե ոչ՝ ցույց տվեք "No image"
        if first_image:
            return mark_safe(f'<img src="{first_image.image.url}" width="50" height="50" style="margin-right: 5px;" />')
        else:
            return "No image"

    show_first_image.short_description = 'First Image'

    class Meta:
        model = Product


admin.site.register(Product, ProductAdmin)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview']
    readonly_fields = ('image_preview',)




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
