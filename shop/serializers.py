from django.db.models import DecimalField
from rest_framework import serializers
from .models import Category, SubCategory, Product, Image, Color, Size, Slider, Brand, DiscountedShowModel, \
      Wishlist, Review, Currency, SizePrice
from decimal import Decimal
from rest_framework import serializers
from .models import Category, SubCategory



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


    class Meta:
        model = Product
        fields = [
            'id', 'name', 'image', 'price', 'final_price',
            'colors', 'brand', 'size', 'liked',
        ]

    def get_liked(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Wishlist.objects.filter(user=user, product=obj).exists()
        return False

    def get_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք
        return obj.price * conversion_rate

    def get_final_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք

        final_price = obj.get_final_price()  # Product մոդելի մեթոդը
        return final_price * conversion_rate if final_price is not None else None



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


class SizePriceSerializer(serializers.ModelSerializer):
    size = SizeSerializer()  # Վերադարձնում ենք չափսի տվյալները

    class Meta:
        model = SizePrice
        fields = ['size', 'price']



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





    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'price', 'final_price', 'colors', 'size', 'brand', 'description', 'delivery_service',
                  'tags', 'liked', 'size_prices']


    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]


    def get_liked(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Wishlist.objects.filter(user=user, product=obj).exists()

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


    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product', 'added_at', 'notified']


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


