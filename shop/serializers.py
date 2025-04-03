from django.db.models import DecimalField
from rest_framework import serializers
from .models import Category, SubCategory, Product, Image, Color, Size, Slider, Brand, DiscountedShowModel, \
      Wishlist, Review, Currency, SizePrice
from decimal import Decimal
from rest_framework import serializers
from .models import Category, SubCategory
from .simliar_products import get_similar_products_ml
from cart.models import CartItem





class SizePriceSerializer(serializers.ModelSerializer):
    size = serializers.SerializerMethodField()


    class Meta:
        model = SizePrice
        fields = ['id', 'price', 'size']


    def get_size(self, obj):
        return {"name": obj.size.name, "slug": obj.size.slug}






class SubcategorySerializer(serializers.ModelSerializer):


    class Meta:
        model = SubCategory
        fields = ["id", "name", "slug", "image"]



class CategoryArajarkvoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'image', 'name', 'slug']



class PriceCurrencySerializer(serializers.Serializer):
    price_currency = serializers.ChoiceField(
        choices=["USD", "AMD", "RUB"],  # ✅ Ընդունում ենք միայն նշված արժույթները
        required=False
    )




    def get_conversion_rate(self, currency_code):
        try:
            currency = Currency.objects.get(code=currency_code)
            return currency.exchange_rate
        except Currency.DoesNotExist:
            return Decimal(1.0)





class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Category
        fields = ["id", "name", 'slug', 'image', "subcategories"]




class LikedSerializer(serializers.Serializer):
    liked = serializers.BooleanField(default=False)








class ImageSerializer(serializers.ModelSerializer):

    image = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ["id", "image"]


    def get_image(self, obj):
        if obj.image:
            return obj.image.url  # վերադարձնում է միայն համեմատական URL (ոչ լրիվ)
        return None


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["id", "name", 'slug', 'hex_code']

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ["id", "name", 'slug']



class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug']




class ProductListSerializer(serializers.ModelSerializer):
    image = ImageSerializer(many=True)
    colors = ColorSerializer(many=True)
    brand = BrandSerializer()
    size = SizeSerializer(many=True)
    liked = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    currency_code = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    count_reviews = serializers.SerializerMethodField()
    in_cart = serializers.SerializerMethodField()
    size_prices = SizePriceSerializer(many=True, read_only=True)


    wishlist_price = serializers.SerializerMethodField()
    wishlist_final_price = serializers.SerializerMethodField()




    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'image', 'price', 'final_price',
            'colors', 'brand', 'size', 'liked', 'currency_code',
            'average_rating', 'count_reviews', 'in_cart', 'size_prices', 'wishlist_price', 'wishlist_final_price'
        ]

    def get_liked(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Wishlist.objects.filter(user=user, product=obj).exists()
        return False

    def get_in_cart(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return CartItem.objects.filter(cart__user=request.user, product=obj).exists()
        return False

    def get_average_rating(self, obj):
        return obj.average_rating()


    def get_count_reviews(self, obj):
        return obj.reviews.filter(status='AP').count()


    def get_currency_code(self, obj):
        request = self.context.get('request')
        return obj.currency_code(request)


    def get_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք
        return obj.price * conversion_rate

    def get_final_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք

        final_price = obj.get_final_price()  # Product մոդելի մեթոդը
        return final_price * conversion_rate if final_price is not None else None



    def get_wishlist_price(self, obj):
        """Վերադարձնում է Wishlist-ի գինը, եթե կա"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            wishlist_item = Wishlist.objects.filter(user=request.user, product=obj).first()
            if wishlist_item:
                return wishlist_item.price
        return None

    def get_wishlist_final_price(self, obj):
        """Վերադարձնում է Wishlist-ի վերջնական գինը, եթե կա"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            wishlist_item = Wishlist.objects.filter(user=request.user, product=obj).first()
            if wishlist_item:
                return wishlist_item.get_final_price()
        return None



class ProductListFilterSerializer(serializers.Serializer):
    colors = ColorSerializer(required=False)
    brand =  BrandSerializer(required=False)
    size = SizeSerializer(required=False)


class DiscountedShowSerializer(serializers.ModelSerializer):
    discount_char = serializers.SerializerMethodField()

    class Meta:
        model = DiscountedShowModel
        fields = ['id', 'image', 'discount_char']

    def get_discount_char(self, obj):
        return obj.get_discount_char()

class ProductListFilterPostSerializer(serializers.Serializer):
    category = serializers.CharField(required=False, allow_blank=True)
    subcategory = serializers.CharField(required=False, allow_blank=True)
    colors = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True
    )
    brand = serializers.ListField(
        child=serializers.CharField(),  # եթե slug-ները եք ուղարկում
        required=False
    )
    size = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True
    )
    min_price = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, allow_null=True
    )
    max_price = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, allow_null=True
    )
    discounted = serializers.BooleanField(default=False)














class RelatedProductSerializer(serializers.ModelSerializer):
    first_image = serializers.SerializerMethodField()


    class Meta:
        model = Product
        fields = ['id', 'slug', 'first_image']


    def get_first_image(self, obj):
        return obj.get_first_image()




class ReviewRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['user', 'rating', 'comment', 'created_at']




class ProductDetailSerializer(serializers.ModelSerializer):
    image = ImageSerializer(many=True)
    colors = ColorSerializer(many=True)
    size = SizeSerializer(many=True)
    size_prices = SizePriceSerializer(many=True, read_only=True)
    brand = BrandSerializer()
    tags = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    related_products = RelatedProductSerializer(many=True, read_only=True)
    similar_products = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    in_cart = serializers.SerializerMethodField()
    count_reviews = serializers.SerializerMethodField()
    currency_code = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()








    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'image', 'price', 'final_price', 'colors', 'size', 'brand', 'description', 'delivery_service',
                  'tags', 'liked', 'size_prices', 'related_products', 'article', 'gender', 'composition', 'created', 'updated', 'similar_products',
                  'average_rating', 'count_reviews', 'currency_code', 'reviews', 'in_cart']


    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]



    def get_currency_code(self, obj):
        request = self.context.get('request')
        return obj.currency_code(request)

    def get_reviews(self, obj):
        reviews = obj.reviews.filter(status=Review.Status.APPROVED, rating=5).order_by('-created_at')[:10]

        return ReviewSerializer(reviews, many=True).data


    def get_average_rating(self, obj):
        return obj.average_rating()


    def get_count_reviews(self, obj):
        return obj.reviews.filter(status='AP').count()

    def get_in_cart(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            size_id = request.query_params.get('size_id')
            cart_items = CartItem.objects.filter(cart__user=request.user, product=obj)

            if size_id:
                cart_items = cart_items.filter(size=size_id)

            return cart_items.exists()
        return False

    def get_similar_products(self, obj):

        similar_products = get_similar_products_ml(obj)
        return ProductListSerializer(similar_products,  many=True, context=self.context).data






    def get_liked(self, obj):
        user = self.context['request'].user
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            size_id = request.query_params.get('size_id')

            detail_liked = Wishlist.objects.filter(user=user, product=obj)

            if size_id:
                detail_liked = detail_liked.filter(size=size_id)

            return detail_liked.exists()
        return False

    def get_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք փոխարժեքը

        size_id = request.query_params.get('size_id')
        if size_id:
            size_price = obj.size_prices.filter(size__id=size_id).first()
            if size_price:
                return size_price.price * conversion_rate

        return obj.price * conversion_rate

    def get_final_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք փոխարժեքը

        size_id = request.query_params.get('size_id')
        if size_id:
            size_price = obj.size_prices.filter(size__id=size_id).first()
            if size_price:
                final_price = size_price.price - (size_price.price * obj.discount_percentage / 100)
                return final_price * conversion_rate

        final_price = obj.get_final_price()
        return final_price * conversion_rate if final_price is not None else None


class UserTokenCheckSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)



class SliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slider
        fields = ['id', 'name', 'image']





class ProductFilterSerializer(serializers.Serializer):
    brand = BrandSerializer(many=True)
    colors = ColorSerializer(many=True)
    sizes = SizeSerializer(many=True)





class ChatGPTPost(serializers.ModelSerializer):
    model = Product
    fields = '__all__'







class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()
    size = SizePriceSerializer(required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_price = serializers.SerializerMethodField()


    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'size', 'price', 'added_at', 'notified', 'final_price']

    # def get_size(self, obj):
    #     if obj.size_price and obj.size_price.size:
    #         return {"name": obj.size_price.size.name, "price": obj.size_price.price, "slug": obj.size_price.size.slug}
    #     return None



    def get_final_price(self, obj):
        return obj.get_final_price()












class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'rating', 'comment', 'created_at', 'status']
        read_only_fields = ['user', 'status']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5')
        return value


    def create(self, validated_data):

        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)





class ProductSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name']


