from django.db.models import DecimalField
from rest_framework import serializers
from .models import Category, SubCategory, Product, Image, Color, Size, Slider, Brand

from rest_framework import serializers
from .models import Category, SubCategory



class SubcategorySerializer(serializers.ModelSerializer):


    class Meta:
        model = SubCategory
        fields = ["id", "name", "slug", "image"]






class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True, required=False)


    class Meta:
        model = Category
        fields = ["id", "name", 'slug', "subcategories"]




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
        fields = ['id', 'name', 'image', 'price', 'colors', 'brand', 'size']


class ProductListFilterSerializer(serializers.Serializer):
    colors = ColorSerializer(required=False)
    brand =  BrandSerializer(required=False)
    size = SizeSerializer(required=False)


class ProductListFilterPostSerializer(serializers.Serializer):
    category = serializers.CharField(required=False)
    subcategory = serializers.CharField(required=False)
    colors = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    brand = serializers.ListField(
        child=serializers.CharField(),  # եթե slug-ները եք ուղարկում
        required=False
    )
    size = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    min_price = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, min_value=0.01
    )
    max_price = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, min_value=0.01
    )






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







