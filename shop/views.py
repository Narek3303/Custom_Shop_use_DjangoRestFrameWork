from django.core.exceptions import FieldError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import Category, SubCategory, Product, Slider, Brand, Image, Size, Color
from .serializers import CategorySerializer, SubcategorySerializer, ProductListSerializer, ProductDetailSerializer, \
    UserTokenCheckSerializer, SliderSerializer, ImageSerializer, ColorSerializer, SizeSerializer, BrandSerializer, \
    ProductFilterSerializer, ProductListFilterSerializer, ProductListFilterPostSerializer

import io
from rest_framework.parsers import JSONParser



class CategoryView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response({

            "data": serializer.data
        }, status=status.HTTP_200_OK)





class ProductListView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ProductListSerializer



    def get(self, request, category_slug=None, subcategory_slug=None):



        category = None
        subcategory = None

        products = Product.objects.filter(available=True, status=Product.Status.PUBLISHED)
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            subcategories = SubCategory.objects.filter(category=category)
            products = products.filter(category__in=subcategories)

        if subcategory_slug:
            subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category)
            products = products.filter(category=subcategory)

        serialized_products = ProductListSerializer(products, many=True).data
        return Response({
            "products": serialized_products,
        }, status=status.HTTP_200_OK)

# class ProductFilterListView(APIView):
#     permission_classes = (AllowAny,)
#     serializer_class = ProductListSerializer
#
#     def get(self, request, category_slug=None, subcategory_slug=None):
#
#         category = None
#         subcategory = None
#
#         products = Product.objects.filter(available=True, status=Product.Status.PUBLISHED)
#         if category_slug:
#             category = get_object_or_404(Category, slug=category_slug)
#             subcategories = SubCategory.objects.filter(category=category)
#             products = products.filter(category__in=subcategories)
#
#         if subcategory_slug:
#             subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category)
#             products = products.filter(category=subcategory)
#
#         serialized_products = ProductListSerializer(products, many=True).data
#         return Response({
#             "products": serialized_products,
#         }, status=status.HTTP_200_OK)



#


        # ✅ Գնի ֆիլտր (min_price & max_price)
        # min_price = request.GET.get("min_price")
        # max_price = request.GET.get("max_price")
        #
        # if min_price:
        #     products = products.filter(price__gte=min_price)  # ✅ `gte` -> greater than or equal
        # if max_price:
        #     products = products.filter(price__lte=max_price)
        #
        # serialized_products = ProductListSerializer(products, many=True).data
        # return Response({"products": serialized_products}, status=status.HTTP_200_OK)




class ProductDetailView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, slug, product_id):
        """
        Returns detailed information about a product and some similar products based on tags.
        """
        product = get_object_or_404(
            Product, id=product_id, slug=slug, available=True, status=Product.Status.PUBLISHED
        )

        similar_products = Product.objects.filter(
            tags__in=product.tags.values_list('id', flat=True),
            status=Product.Status.PUBLISHED
        ).exclude(id=product.id)

        similar_products = similar_products.annotate(
            same_tags=Count('tags')
        ).order_by('-same_tags', '-created')[:20]

        return Response({
            'product': ProductDetailSerializer(product).data,
            'similar_products': ProductDetailSerializer(similar_products, many=True).data,
        }, status=status.HTTP_200_OK)


class UserTokenCheckView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserTokenCheckSerializer

    def post(self, request):
        """
        Validates the provided user token.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            if Token.objects.filter(key=token).exists():
                return Response({'message': 'Valid token'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SliderListAPIView(APIView):
    def get(self, request):
        """
        Fetches the latest 4 sliders for the homepage carousel.
        """
        sliders = Slider.objects.all()[:4]
        serializer = SliderSerializer(sliders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductFilterView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        """
        Fetches all categories, brands, colors, and sizes for product filtering.
        """
        categories = Category.objects.all()
        brands = Brand.objects.all()
        colors = Color.objects.all()
        sizes = Size.objects.all()

        category_serializer = CategorySerializer(categories, many=True)
        brand_serializer = BrandSerializer(brands, many=True)
        color_serializer = ColorSerializer(colors, many=True)
        size_serializer = SizeSerializer(sizes, many=True)

        return Response({
            'categories': category_serializer.data,
            'brands': brand_serializer.data,
            'colors': color_serializer.data,
            'sizes': size_serializer.data
        }, status=status.HTTP_200_OK)


def create_products(request):
    """
    Creates a set of sample products for testing purposes.
    """
    category = Category.objects.first()  # Get the first category
    subcategory = SubCategory.objects.first()  # Get the first subcategory
    brand = Brand.objects.first()  # Get the first brand
    size = Size.objects.first()  # Get the first size
    color = Color.objects.first()  # Get the first color

    # Generate 10 sample products
    products = [
        Product(
            name=f'Product {i+1}',
            slug=f'product-{i+1}',
            category=subcategory,
            brand=brand,
            price=100 + i * 10,  # Price increases per product
            available=True,
            description=f'Description for product {i+1}',
        )
        for i in range(10)
    ]

    # Bulk create all products at once
    Product.objects.bulk_create(products)

    return JsonResponse({'status': 'Products created successfully!'}, status=status.HTTP_201_CREATED)



class ProductFilterListView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ProductListFilterPostSerializer

    def post(self, request):
        # Վավերացնում ենք request-ի տվյալները
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Վավերացված տվյալները
        validated_data = serializer.validated_data

        # Ֆիլտրում ենք սկզբնական queryset-ը
        products = Product.objects.filter(available=True, status=Product.Status.PUBLISHED)

        # ✅ Կատեգորիայի ֆիլտր
        # ✅ Կատեգորիայի ֆիլտր
        category_slug = validated_data.get('category')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            subcategories = SubCategory.objects.filter(category=category)
            products = products.filter(category__in=subcategories)  # ⬅️ Փոխվել է subcategory֊ից category


            # ✅ Ենթակատեգորիայի ֆիլտր
        subcategory_slug = validated_data.get('subcategory')
        if category_slug and subcategory_slug:
            subcategory = get_object_or_404(SubCategory, slug=subcategory_slug)
            products = products.filter(category=subcategory)  # ⬅️ Նորից category֊ով



        # ✅ Բրենդի ֆիլտր (Multiple Choice)
        brand_slugs = validated_data.get('brand')
        if brand_slugs:
            brands = Brand.objects.filter(slug__in=brand_slugs)  # ստանում ենք brand-ների օբյեկտները slug-ներով
            products = products.filter(brand__in=brands).distinct()  # ֆիլտրում ենք brand-ների համաձայն

        # ✅ Գույների ֆիլտր (Multiple Choice)
        colors_slug = validated_data.get('colors')
        if colors_slug:
            products = products.filter(colors__slug__in=colors_slug).distinct()

        # ✅ Չափերի ֆիլտր (Multiple Choice)
        size_slugs = validated_data.get('size')
        if size_slugs:
            products = products.filter(size__slug__in=size_slugs).distinct()


        # ✅ Գին (Min/Max)
        min_price = validated_data.get('min_price')
        max_price = validated_data.get('max_price')

        if min_price is not None:
            products = products.filter(price__gte=min_price)

        if max_price is not None:
            products = products.filter(price__lte=max_price)

        # ✅ Սերիալիզացնում ենք արդյունքները
        serialized_products = ProductListSerializer(products, many=True).data

        return Response({"products": serialized_products}, status=status.HTTP_200_OK)