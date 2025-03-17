
from django.core.cache import cache
from django.core.exceptions import FieldError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
from cart.cart import Cart

from .models import Category, SubCategory, Product, Slider, Brand, Image, Size, Color, DiscountedShowModel, Wishlist, \
                        Review, Currency

from .serializers import CategorySerializer, SubcategorySerializer, ProductListSerializer, ProductDetailSerializer, \
    UserTokenCheckSerializer, SliderSerializer, ImageSerializer, ColorSerializer, SizeSerializer, BrandSerializer, \
    ProductFilterSerializer, ProductListFilterSerializer, ProductListFilterPostSerializer, ChatGPTPost, CategoryArajarkvoxSerializer, \
    DiscountedShowSerializer, ReviewSerializer, CartAddPostSerializer


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
        discount_char = DiscountedShowModel.objects.filter(available=True).last()
        serialized_discount_char = DiscountedShowSerializer(discount_char).data if discount_char else None
        return Response({
            "discount_char_vi": serialized_discount_char,
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


        return Response({

            "products": serialized_products,
        }, status=status.HTTP_200_OK)



class ProductDetailView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ProductDetailSerializer

    def get(self, request, slug, product_id):
        """
        Returns detailed information about a product and some similar products based on tags.
        """
        product = get_object_or_404(
            Product, id=product_id, slug=slug, available=True, status=Product.Status.PUBLISHED
        )

        # Ստանում ենք փոխարժեքը middleware-ից
        conversion_rate = getattr(request, 'conversion_rate', 1.0)

        # Գտնում ենք նմանատիպ ապրանքները ըստ tag-երի
        similar_products = Product.objects.filter(
            tags__in=product.tags.values_list('id', flat=True),
            status=Product.Status.PUBLISHED
        ).exclude(id=product.id)

        similar_products = similar_products.annotate(
            same_tags=Count('tags')
        ).order_by('-same_tags', '-created')[:20]

        return Response({
            'product': ProductDetailSerializer(
                product, context={'request': request}
            ).data,
            'similar_products': ProductDetailSerializer(
                similar_products, many=True, context={'request': request}
            ).data,
        }, status=status.HTTP_200_OK)





class CartAddAPIView(APIView):
    """
    Add a product to the cart.
    """
    serializer_class = CartAddPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id):
        cart = Cart(request)

        # Ստանում ենք ապրանքը
        product = get_object_or_404(Product, id=product_id, available=True, status=Product.Status.PUBLISHED)

        # Ստուգում ենք փոխանցված տվյալները
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        color_slug = serializer.validated_data.get('color', None)
        size_id = serializer.validated_data.get('size_id', None)
        quantity = serializer.validated_data.get('quantity', 1)
        override = serializer.validated_data.get('override', False)

        # Ստանում ենք փոխարժեքը middleware-ից
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))

        # Ստանում ենք գինը `size_id`-ի հիման վրա
        price, final_price = self.get_product_price(product, size_id, conversion_rate)

        # Ավելացնում ենք զամբյուղում
        cart.add(
            product=product,
            color=color_slug,
            size_id=size_id,
            quantity=quantity,
            override=override,
            price=price,
            final_price=final_price
        )

        return Response({"message": "Product added to cart successfully"}, status=status.HTTP_201_CREATED)

    def get_product_price(self, product, size_id, conversion_rate):
        """
        Հաշվում է գինը և զեղչված գինը ըստ `size_id`-ի։
        """
        if size_id:
            size_price = product.size_prices.filter(size__id=size_id).first()
            if size_price:
                price = size_price.price * conversion_rate
                final_price = price - (price * product.discount_percentage / 100)
                return price, final_price

        # Եթե `size_id` չկա, օգտագործում ենք հիմնական գինը
        price = product.price * conversion_rate
        final_price = product.get_final_price() * conversion_rate if product.get_final_price() else None

        return price, final_price


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
    permission_classes = (AllowAny,)

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


from django.db.models import F, ExpressionWrapper, DecimalField

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

        # Ֆիլտրում ենք ըստ կատեգորիայի
        category_slug = validated_data.get('category')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            subcategories = SubCategory.objects.filter(category=category)
            products = products.filter(category__in=subcategories)

        subcategory_slug = validated_data.get('subcategory')
        if category_slug and subcategory_slug:
            subcategory = get_object_or_404(SubCategory, slug=subcategory_slug)
            products = products.filter(category=subcategory)

        # Ֆիլտրում ենք ըստ բրենդի
        brand_slugs = validated_data.get('brand')
        if brand_slugs:
            brands = Brand.objects.filter(slug__in=brand_slugs)
            products = products.filter(brand__in=brands).distinct()

        # Ֆիլտրում ենք ըստ գույների
        colors_slug = validated_data.get('colors')
        if colors_slug:
            products = products.filter(colors__slug__in=colors_slug).distinct()

        # Ֆիլտրում ենք ըստ չափսերի
        size_slugs = validated_data.get('size')
        if size_slugs:
            products = products.filter(size__slug__in=size_slugs).distinct()

        # Ստանում ենք փոխարժեքը middleware-ից
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))

        # Ավելացնում ենք ֆինալ գինը
        products = products.annotate(
            final_price=ExpressionWrapper(
                F("price") - (F("price") * F("discount_percentage") / 100),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )

        # Ստանում ենք min/max գները
        min_price = validated_data.get('min_price')
        max_price = validated_data.get('max_price')

        # Փոխակերպում ենք min/max գները հիմնական արժույթից
        if min_price is not None:
            min_price = Decimal(min_price) / conversion_rate

        if max_price is not None:
            max_price = Decimal(max_price) / conversion_rate

        # Սահմանում ենք գների ֆիլտրի դաշտը
        price_field = 'final_price' if discounted else 'price'
        price_filter = {}

        if min_price is not None:
            price_filter[f"{price_field}__gte"] = min_price

        if max_price is not None:
            price_filter[f"{price_field}__lte"] = max_price

        if price_filter:
            products = products.filter(**price_filter)

        # Սերիալիզացնում ենք արդյունքը
        serialized_products = ProductListSerializer(
            products,
            many=True,
            context={'request': request}
        ).data

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

    def get(self, request, product_id):
        product = Product.objects.get(id=product_id)

        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)


        if not created:
            wishlist_item.delete()
            return Response({'message': 'Removed from wishlist',
                             "id": product_id,
                             "liked": False}, status=status.HTTP_200_OK)

        return Response({'message': 'Added to wishlist',
                         "id": product_id,
                         "liked": True
                         }, status=status.HTTP_201_CREATED)


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




class ProductPriceView(APIView):
    def get(self, request, product_id, currency_code):
        try:
            product = Product.objects.get(id=product_id)
            final_price = product.get_price_in_currency(currency_code)
            if final_price is not None:
                return Response({'price': final_price}, status=status.HTTP_200_OK)
            return Response({'error': 'Currency not found'}, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)



def convert_price(request, product_id, currency_code):
    product = get_object_or_404(Product, id=product_id)
    converted_price = product.get_price_in_currency(currency_code)

    if converted_price is not None:
        return JsonResponse({"converted_price": converted_price, "currency": currency_code})
    return JsonResponse({"error": "Currency not supported"}, status=400)




class SetCurrencyAPIView(APIView):
    """
    API որը թույլ է տալիս ընտրել արժույթը և պահպանել session-ում կամ cache-ում:
    """

    def post(self, request):
        price_currency = request.data.get('price_currency', 'USD')

        # Ստուգում ենք՝ արդյոք տվյալ արժույթը առկա է մոդելում
        if not Currency.objects.filter(code=price_currency).exists():
            return Response({"error": "Invalid currency code"}, status=status.HTTP_400_BAD_REQUEST)

        # Պահպանում ենք արժեքը session-ում
        request.session['price_currency'] = price_currency

        # Պահպանում ենք cache-ում (եթե օգտատերը authentication ունի)
        if request.user.is_authenticated:
            cache.set(f"user_currency_{request.user.id}", price_currency, timeout=60 * 60 * 24)

        return Response({"message": f"Currency set to {price_currency}"}, status=status.HTTP_200_OK)


class GetAvailableCurrenciesAPIView(APIView):
    """
    API որը վերադարձնում է առկա արժույթները և դրանց փոխարժեքները:
    """

    def get(self, request):
        currencies = Currency.objects.all().values("code", "exchange_rate")
        return Response({"currencies": list(currencies)}, status=status.HTTP_200_OK)


