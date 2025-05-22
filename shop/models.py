import uuid
from django.utils.text import slugify
from django.db import models
from django.utils.html import mark_safe
from django.urls import reverse
from taggit.managers import TaggableManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.core.mail import send_mail
from rest_framework import serializers, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _



User = get_user_model()



class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Product.Status.PUBLISHED)


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, null=True, unique=True)
    image = models.ImageField('Category Image', upload_to='category_image/%Y/%m/%d', null=True)
    is_recommended = models.BooleanField(default=False, null=True, blank=True)


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
        DRAFT = 'DF', _('Draft')  # Черновик | Նախագիծ
        PUBLISHED = 'PB', _('Published')  # Опубликовано | Հրապարակված

    category = models.ForeignKey(
        SubCategory,
        related_name='products',
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_('Category')  # Категория | Կատեգորիա
    )
    name = models.CharField(
        _('Product Name'),  # Название товара | Ապրանքի անուն
        max_length=200
    )
    slug = models.SlugField(
        _('Slug'),  # Слаг | Սլագ
        max_length=200,
        blank=True
    )
    brand = models.ForeignKey(
        'Brand',
        verbose_name=_('Brand'),  # Бренд | Ապրանքանիշ
        related_name='products',
        null=True,
        on_delete=models.CASCADE
    )
    image = models.ManyToManyField(
        'Image',
        verbose_name=_('Images'),  # Изображения | Նկարներ
        related_name='products'
    )
    size = models.ManyToManyField(
        'Size',
        blank=True,
        verbose_name=_('Sizes'),  # Размеры | Չափսեր
        related_name='products'
    )
    colors = models.ManyToManyField(
        'Color',
        related_name="products",
        verbose_name=_('Colors')  # Цвета | Գույներ
    )
    description = models.TextField(
        _('Product Description'),  # Описание товара | Ապրանքի նկարագրություն
        blank=True
    )
    delivery_service = models.TextField(
        _('Delivery Service'),  # Условия доставки | Առաքման ծառայություն
        blank=True,
        null=True
    )
    price = models.DecimalField(
        _('Price (AMD)'),  # Цена (AMD) | Գին (Դրամ)
        max_digits=10,
        decimal_places=2
    )
    stock = models.PositiveIntegerField(
        _('Stock'),  # Наличие | Պաշար
        default=0
    )
    weight = models.DecimalField(
        _("Weight (kg)"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True
    )
    discount_percentage = models.DecimalField(
        _('Discount Percentage'),  # Процент скидки | Զեղչի տոկոս
        max_digits=10,
        decimal_places=2,
        default=0,
        null=True
    )
    related_products = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        verbose_name=_('Related Products')  # Связанные товары | Կապված ապրանքներ
    )
    available = models.BooleanField(
        _('Available'),  # В наличии | Մատչելի
        default=True
    )
    created = models.DateTimeField(
        _('Created'),  # Создан | Ստեղծված
        auto_now_add=True
    )
    updated = models.DateTimeField(
        _('Updated'),  # Обновлено | Թարմացված
        auto_now=True
    )
    status = models.CharField(
        _('Status'),  # Статус | Կարգավիճակ
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT
    )
    tags = TaggableManager(
        verbose_name=_('Tags')  # Теги | Պիտակներ
    )
    objects = models.Manager()
    published = PublishedManager()
    article = models.CharField(
        _('Article'),  # Артикул | Արտիկուլ
        max_length=20,
        unique=True,
        blank=True
    )
    composition = models.CharField(
        _('Composition'),  # Состав | Բաղադրություն
        max_length=255,
        blank=True
    )

    GENDER_CHOICES = [
        ('Мужской', _('Men')),  # Мужской | Տղամարդ
        ('Женский', _('Women')),  # Женский | Կին
        ('Унисекс', _('Unisex'))  # Унисекс | Ունիսեքս
    ]
    gender = models.CharField(
        _('Gender'),  # Пол | Սեռ
        max_length=10,
        blank=True,
        choices=GENDER_CHOICES
    )

    fit_type = models.CharField(
        _('Fit Type'),  # Тип посадки | Հագուստի տեսակ
        max_length=50,
        blank=True
    )
    pocket_type = models.CharField(
        _('Pocket Type'),  # Тип кармана | Պարկուճի տեսակ
        max_length=100,
        blank=True
    )
    model_features = models.CharField(
        _('Model Features'),  # Особенности модели | Մոդելի առանձնահատկություններ
        max_length=255,
        blank=True
    )
    care_instructions = models.CharField(
        _('Care Instructions'),  # Инструкции по уходу | Պահպանման կանոններ
        max_length=255,
        blank=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Product')  # Товар | Ապրանք
        verbose_name_plural = _('Products')  # Товары | Ապրանքներ
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug, self.id])

    def get_final_price(self):
        if self.discount_percentage and self.discount_percentage > 0:
            discount_amount = (self.discount_percentage / 100) * self.price
            return self.price - discount_amount
        return None

    def get_price(self):
        currency = Currency.objects.filter(code="")


    def get_same_product_different(self):
        return self.related_products.exclude(id=self.id)


    def get_price_for_size(self, size):
        """
        Ստանում ենք ապրանքի գինը ըստ չափսի
        """
        # Այս ֆունկցիայի մեջ պետք է որոշել, թե ինչպես է ստացվում գինը:
        size_price = self.size_prices.get(size=size)  # example if there is a relation to price per size
        return size_price


    def average_rating(self):
        reviews = self.reviews.filter(status=Review.Status.APPROVED)

        total_rating = sum(review.rating for review in reviews)
        count = reviews.count()


        if count > 0:
            return total_rating / count
        else:
            return 0



    def check_stock(self):
        """Ստուգում է պահեստի քանակը և եթե անհրաժեշտ է՝ ուղարկում զգուշացում"""
        if self.stock < 10:
            self.send_alert()


    def send_alert(self):
        """Ուղարկում է ծանուցում պահեստի ցածր լինելու մասին"""
        message = f"Product '{self.name}' has low stock! Only {self.stock} left."
        try:
            send_mail(
                "Low Stock Alert",
                "Product X is running low on stock!",
                "noreply@NSCompany.com",
                ["margaryannarek056@gmail.com"],
                fail_silently=False  # Թող բարձրացնի բացառություն
            )
        except Exception as e:
            print(f"❌ Email sending failed: {e}")


    def get_first_image(self):
        first_image = self.image.first()
        return first_image.image.url if first_image else None


    def save(self, *args, **kwargs):
        if not self.article:
            self.article = self.generate_unique_article()

        if not self.slug:
            self.slug = f'{slugify(self.name)}-{uuid.uuid4()}'
        super().save(*args, **kwargs)

    def generate_unique_article(self):
        return str(uuid.uuid4().hex[:10]).upper()


    def currency_code(self, request):
        price_currency = getattr(request, 'currency_code')
        return price_currency

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

    class Meta:
        ordering = ['name']          # <— սա է հարթում pagination-ի անորոշությունը
        verbose_name = 'Size'
        verbose_name_plural = 'Sizes'


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



class DiscountedShowModel(models.Model):
    image = models.ImageField("Image", upload_to='DiscountedShow/%Y/%m/%d')
    min_discount = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    max_discount = models.IntegerField(
        default=2,
        validators=[MinValueValidator(2), MaxValueValidator(100)],
    )


    def get_discount_char(self):
        return f'{self.min_discount} - {self.max_discount} %'

    available = models.BooleanField(default=False)



class SizePrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="size_prices")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)














class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(SizePrice, on_delete=models.SET_NULL, null=True)  # Ավելացրեք չափսը
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False, null=True)

    class Meta:
        unique_together = ('user', 'product', 'size')  # Ուշադրություն՝ ավելացնել unique_together՝ հաշվի առնելով չափսը

    def get_final_price(self):
        if self.product.discount_percentage and self.product.discount_percentage > 0:
            discount_amount = (self.product.discount_percentage / 100) * self.price
            final_price = self.price - discount_amount
            return final_price
        # Եթե զեղչ չկա, վերադարձնենք հենց ինքնին գինը
        return self.price









class Review(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PD', 'Pending'
        APPROVED = 'AP', 'Approved'
        REJECTED = 'RJ', 'Rejected'

    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=2, choices=Status.choices, default=Status.APPROVED
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.rating}⭐)"

    def send_notification(self):
        """ Notify the admin about the new review """
        send_mail(
            subject=f'New Review for {self.product.name}',
            message=f'Review from {self.user.email}:\nRating: {self.rating}\nComment: {self.comment}',
            from_email='noreply@yourshop.com',
            recipient_list=['admin@yourshop.com']
        )




class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)  # USD, EUR, AMD
    name = models.CharField(max_length=50)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)  # 1 USD = X

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.exchange_rate}"

    class Meta:
        ordering = ['code']

    def get_price_in_currency(self, price_in_usd):
        """Փոխակերպում է գինը USD-ից տվյալ արժույթով"""
        if self.exchange_rate and price_in_usd is not None:
            return round(price_in_usd * self.exchange_rate, 2)
        return None

    def save(self, *args, **kwargs):
        if self.exchange_rate <= 0:
            raise ValueError("Exchange rate must be greater than zero.")
        super().save(*args, **kwargs)

    @classmethod
    def get_base_currency(cls):
        """Վերադարձնում է հիմնական արժույթը (օրինակ՝ USD)"""
        return cls.objects.filter(exchange_rate=1.0).first()





