from django.db import models
from django.urls import reverse
from django.db import models
from django.utils.html import mark_safe
from taggit.managers import TaggableManager





class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset().filter(status=Product.Status.PUBLISHED)
        )


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name



class SubCategory(models.Model):
        category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
        name = models.CharField('Կատեգորիայի անվանումը', max_length=200)
        slug = models.SlugField(max_length=200, unique=True)
        image = models.ImageField('Ենթակատեգորիայի Նկար', upload_to='subcategory_image/%Y/%m/%d', null=True)

        class Meta:
            ordering = ['name']
            indexes = [
                models.Index(fields=['name']),
            ]
            verbose_name = 'Subcategory'
            verbose_name_plural = 'Subcategories'

        def __str__(self):
            return self.name






class Product(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    category = models.ForeignKey(
        SubCategory,
        related_name='products',
        on_delete=models.CASCADE,
        null=True
    )
    name = models.CharField('Անուն',max_length=200)
    slug = models.SlugField(max_length=200)
    image = models.ManyToManyField('Image', verbose_name='Նկարներ', related_name='images')
    size = models.ManyToManyField('Size', verbose_name='Չափսեր', related_name='sizes')
    colors = models.ManyToManyField('Color', related_name="colorsmodel", null=True)
    description = models.TextField('Ապրանքի նկարագրություն', blank=True)
    delivery_service = models.TextField('Առաքման ծառայություն', blank=True, null=True)
    price = models.DecimalField('Գին',max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2,
        choices=Status,
        default=Status.DRAFT
    )
    objects = models.Manager()
    published = PublishedManager()
    tags = TaggableManager(verbose_name='Բրենդ')

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return self.name





class Image(models.Model):
    image = models.ImageField('Նկար', upload_to='products/%Y/%m/%d', blank=True)

    def image_preview(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="100" height="100" style="border-radius: 5px;" />')
        return "No Image"


    def __str__(self):
        return f"Image {self.id}"



class Size(models.Model):
    name = models.CharField('Չափս', max_length=6)


    def __str__(self):
        return self.name



class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, unique=True)  # Example: "#FF5733"

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.hex_code})"


class Slider(models.Model):
    name = models.CharField('Անուն', max_length=200)
    image = models.ImageField('Կարուսելի պատկեր', upload_to='carousel_image/%Y/%m/%d')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name


    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]