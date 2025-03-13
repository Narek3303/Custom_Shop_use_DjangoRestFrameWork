from django.core.exceptions import FieldError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import Category, SubCategory, Product, Slider, Brand, Image, Size, Color, DiscountedShowModel, Wishlist, \
                        Review

from .serializers import CategorySerializer, SubcategorySerializer, ProductListSerializer, ProductDetailSerializer, \
    UserTokenCheckSerializer, SliderSerializer, ImageSerializer, ColorSerializer, SizeSerializer, BrandSerializer, \
    ProductFilterSerializer, ProductListFilterSerializer, ProductListFilterPostSerializer, ChatGPTPost, CategoryArajarkvoxSerializer, \
    DiscountedShowSerializer, ReviewSerializer


from rest_framework import generics, permissions
from .models import Wishlist
from .serializers import WishlistSerializer
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

        # Wishlist-ի ստուգում
        serialized_products = ProductListSerializer(products, many=True, context={'request': request}).data
        discount_char = DiscountedShowModel.objects.filter(available=True).last()
        serialized_discount_char = DiscountedShowSerializer(discount_char).data if discount_char else None

        return Response({
            "discount_char_vi": serialized_discount_char,
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
        category_arajarkvox = Category.objects.filter(is_recommended=True)[:4]
        categories = Category.objects.all()
        brands = Brand.objects.all()
        colors = Color.objects.all()
        sizes = Size.objects.all()


        category_arajarkvox_serializer = CategoryArajarkvoxSerializer(category_arajarkvox, many=True)
        category_serializer = CategorySerializer(categories, many=True)
        brand_serializer = BrandSerializer(brands, many=True)
        color_serializer = ColorSerializer(colors, many=True)
        size_serializer = SizeSerializer(sizes, many=True)

        return Response({
            'is_recommended': category_arajarkvox_serializer.data,
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
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        discounted = validated_data.get('discounted', False)

        products = Product.objects.filter(available=True, status=Product.Status.PUBLISHED)

        if discounted:
            products = products.filter(discount_percentage__gt=0)

        category_slug = validated_data.get('category')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            subcategories = SubCategory.objects.filter(category=category)
            products = products.filter(category__in=subcategories)

        subcategory_slug = validated_data.get('subcategory')
        if category_slug and subcategory_slug:
            subcategory = get_object_or_404(SubCategory, slug=subcategory_slug)
            products = products.filter(category=subcategory)

        brand_slugs = validated_data.get('brand')
        if brand_slugs:
            brands = Brand.objects.filter(slug__in=brand_slugs)
            products = products.filter(brand__in=brands).distinct()

        colors_slug = validated_data.get('colors')
        if colors_slug:
            products = products.filter(colors__slug__in=colors_slug).distinct()

        size_slugs = validated_data.get('size')
        if size_slugs:
            products = products.filter(size__slug__in=size_slugs).distinct()

        min_price = validated_data.get('min_price')
        max_price = validated_data.get('max_price')

        if min_price is not None:
            price_field = 'get_final_price' if discounted else 'price'
            products = products.filter(**{f'{price_field}__gte': min_price})

        if max_price is not None:
            price_field = 'get_final_price' if discounted else 'price'
            products = products.filter(**{f'{price_field}__lte': max_price})

        serialized_products = ProductListSerializer(products, many=True, context={'request': request}).data

        return Response({"products": serialized_products}, status=status.HTTP_200_OK)


# class ChatGPTView(APIView):
#     permission_classes = (AllowAny,)
#     serializer_class = ChatGPTPost
#
#
#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ToggleWishlistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id):
        product = Product.objects.get(id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

        if not created:
            wishlist_item.delete()
            return Response({'message': 'Removed from wishlist'}, status=status.HTTP_200_OK)

        return Response({'message': 'Added to wishlist'}, status=status.HTTP_201_CREATED)


class WishlistProductsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=wishlist_product_ids)
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        reviews = Review.objects.filter(product_id=product_id, status='AP')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request, product_id):
        data = request.data.copy()
        data['product'] = product_id
        serializer = ReviewSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            review = serializer.save()
            review.send_notification()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminReviewModeration(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, review_id):
        review = Review.objects.get(id=review_id)
        action = request.data.get('action')
        if action == 'approve':
            review.status = Review.Status.APPROVED
        elif action == 'reject':
            review.status = Review.Status.REJECTED
        review.save()
        return Response({'message': f'Review {review.status.lower()} successfully'}, status=status.HTTP_200_OK)


