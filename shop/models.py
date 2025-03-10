import uuid
from django.utils.text import slugify
from django.db import models
from django.utils.html import mark_safe
from django.urls import reverse
from taggit.managers import TaggableManager


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Product.Status.PUBLISHED)


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, null=True, unique=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])


class Brand(models.Model):
    name = models.CharField('Brand Name', max_length=40)
    slug = models.SlugField(max_length=200, unique=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('brand_detail', args=[self.slug])


class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField('Subcategory Name', max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField('Subcategory Image', upload_to='subcategory_image/%Y/%m/%d', null=True)
    is_recommended = models.BooleanField(default=False, null=True, blank=True)



    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'Subcategory'
        verbose_name_plural = 'Subcategories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('subcategory_detail', args=[self.slug])





class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    category = models.ForeignKey(SubCategory, related_name='products', on_delete=models.CASCADE, null=True)
    name = models.CharField('Product Name', max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    brand = models.ForeignKey('Brand', verbose_name='Brand', related_name='products', null=True, on_delete=models.CASCADE)
    image = models.ManyToManyField('Image', verbose_name='Images', related_name='products')
    size = models.ManyToManyField('Size', verbose_name='Sizes', related_name='products')
    colors = models.ManyToManyField('Color', related_name="products", blank=True)
    description = models.TextField('Product Description', blank=True)
    delivery_service = models.TextField('Delivery Service', blank=True, null=True)
    price = models.DecimalField('Price', max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField('Discount Percentage', max_digits=10, decimal_places=2, default=0, null=True)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT
    )
    tags = TaggableManager(verbose_name='Tags')
    objects = models.Manager()  # Default manager
    published = PublishedManager()  # Custom manager for published products

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    def get_final_price(self):
        """
        Calculate the final price after applying the discount percentage
        """
        if self.discount_percentage and self.discount_percentage > 0:
            discount_amount = (self.discount_percentage / 100) * self.price
            return self.price - discount_amount
        return self.price


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f'{slugify(self.name)}-{uuid.uuid4()}'
        super().save(*args, **kwargs)

class Image(models.Model):
    image = models.ImageField('Image', upload_to='products/%Y/%m/%d', blank=True)

    def image_preview(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="100" height="100" style="border-radius: 5px;" />')
        return "No Image"

    def __str__(self):
        return f"Image {self.id}"


class Size(models.Model):
    name = models.CharField('Size', max_length=6)
    slug = models.SlugField(max_length=200, null=True, unique=True)

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField('Color', max_length=50, unique=True)
    slug = models.SlugField(max_length=200, null=True, unique=True)
    hex_code = models.CharField('Hex Code', max_length=7, unique=True)  # Example: "#FF5733"

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.hex_code})"


class Slider(models.Model):
    name = models.CharField('Name', max_length=200)
    image = models.ImageField('Carousel Image', upload_to='carousel_image/%Y/%m/%d')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]


