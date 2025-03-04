from django.contrib import admin

from .models import Category, Product, SubCategory, Image, Size, Color


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}




@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}




@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):



    list_display = [
        'name',
        'slug',
        'price',
        'available',
        'created',
        'updated',

    ]
    list_filter = ['available', 'created', 'updated']
    list_editable = ['price', 'available']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['created']
    show_facets = admin.ShowFacets.ALWAYS


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview']
    readonly_fields = ('image_preview',)



@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_code']

