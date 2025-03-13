from django.db.models import DecimalField
from rest_framework import serializers
from .models import Category, SubCategory, Product, Image, Color, Size, Slider, Brand, DiscountedShowModel, \
      Wishlist, Review

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



class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Category
        fields = ["id", "name", 'slug', 'image', "subcategories"]











class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["id", "image"]

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
    brand =  BrandSerializer()
    size = SizeSerializer(many=True)






    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'price', 'get_final_price', 'colors', 'brand', 'size']


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










class ProductDetailSerializer(serializers.ModelSerializer):
    image = ImageSerializer(many=True)
    colors = ColorSerializer(many=True)
    size = SizeSerializer(many=True)
    tags = serializers.SerializerMethodField()


    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'price', 'colors', 'size', 'description', 'tags']

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]




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