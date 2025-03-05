from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import NotFound

from .models import Category, SubCategory, Product, Slider
from .serializers import CategorySerializer, SubcategorySerializer, ProductListSerializer, ProductDetailSerializer, \
    UserTokenCheckSerializer, SliderSerializer
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token


class CategoryView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer



    def get(self, request):

        categories = Category.objects.all()

        serializer = CategorySerializer(categories, many=True)
        content = {"մանրամասն": ("Կոլոր կատեգորիաները և ենթակատեգորիաները")}
        return Response(serializer.data, status=status.HTTP_200_OK)

# class SubcategoryView(APIView):
#     permission_classes = (AllowAny,)
#     serializer_class = SubcategorySerializer
#
#
#
#     def get(self, request):
#         subcategories = SubCategory.objects.all()
#         serializer = SubcategorySerializer(subcategories, many=True)
#         return Response(
#             {
#
#                 "data": serializer.data
#             },
#             status=status.HTTP_200_OK
#         )


class ProductListView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ProductListSerializer



    def get(self, request, category_slug=None, subcategory_slug=None):
        category = None
        subcategory = None
        categories = Category.objects.all()
        subcategories = SubCategory.objects.all()
        products = Product.objects.filter(available=True, status=Product.Status.PUBLISHED)

        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            subcategories = subcategories.filter(category=category)
            products = products.filter(category__in=subcategories)


        if subcategory_slug:
            subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category)
            products = products.filter(category=subcategory)

        # category_data = CategorySerializer(category).data if category else None
        #
        # categories_data = CategorySerializer(categories, many=True).data

        products_data = ProductListSerializer(products, many=True).data

        return Response({
            # 'category': category_data,

            # 'categories': categories_data,

            'products': products_data,
        }, status=status.HTTP_200_OK)




from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Product
from .serializers import ProductDetailSerializer

class ProductDetailView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, slug, product_id):
        product = get_object_or_404(
            Product, id=product_id, slug=slug, available=True, status=Product.Status.PUBLISHED
        )

        post_tags_ids = product.tags.values_list('id', flat=True)

        similar_posts = Product.objects.filter(
            tags__in=post_tags_ids,
            status=Product.Status.PUBLISHED
        ).exclude(id=product.id)

        similar_posts = similar_posts.annotate(
            same_tags=Count('tags')
        ).order_by('-same_tags', '-created')[:20]

        return Response({
            'product': ProductDetailSerializer(product).data,
            'similar_posts': ProductDetailSerializer(similar_posts, many=True).data,
        }, status=200)


class UserTokenCheckView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserTokenCheckSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']  # Use validated_data

            # Check if the token exists
            if Token.objects.filter(key=token).exists():
                return Response({'հաղորդագրություն': 'Վավեր նշան'}, status=status.HTTP_200_OK)

            return Response({'սխալ': 'Անվավեր նշան'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SliderListAPIView(APIView):
    def get(self, request):
        sliders = Slider.objects.all()
        serializer = SliderSerializer(sliders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)