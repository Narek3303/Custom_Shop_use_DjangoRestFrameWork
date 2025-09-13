
from django.core.cache import cache
from django.core.exceptions import FieldError, PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
# from .recommender import Recommender
# from .hybrid_recommender import hybrid_recommendation
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q, Case, When, IntegerField
from .ml_recommender_system import hybrid_recommendation


from .models import Category, SubCategory, Product, Slider, Brand, Image, Size, Color, DiscountedShowModel, Wishlist, \
                        Review, Currency, SizePrice

from .serializers import CategorySerializer, SubcategorySerializer, ProductListSerializer, ProductDetailSerializer, \
    UserTokenCheckSerializer, SliderSerializer, ImageSerializer, ColorSerializer, SizeSerializer, BrandSerializer, \
    ProductFilterSerializer, ProductListFilterSerializer, ProductListFilterPostSerializer, ChatGPTPost, CategoryArajarkvoxSerializer, \
    DiscountedShowSerializer, ReviewSerializer, ReviewRatingSerializer, ProductLikedSerializer
from rest_framework.pagination import PageNumberPagination


from rest_framework import generics, permissions
# from .models import Wishlist
from .serializers import WishlistSerializer
import io
from rest_framework.parsers import JSONParser



class ProductLikedView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            products = Product.objects.filter(wishlist__user=user).distinct()
        else:
            products = Product.objects.none()
        serializer = ProductLikedSerializer(products, many=True, context={'request': request})
        return Response({'products': serializer.data})



class ProductPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100




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


        conversion_rate = getattr(request, 'conversion_rate', 1.0)
        price_currency = getattr(request, 'currency_code')




        return Response({
            'product': ProductDetailSerializer(
                product, context={'request': request}
            ).data
            # 'similar_products': ProductDetailSerializer(
            #     similar_products, many=True, context={'request': request}
            # ).data,
        }, status=status.HTTP_200_OK)





# class CartAddAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request, product_id):
#         cart = Cart(request)
#         product = get_object_or_404(Product, id=product_id, available=True, status=Product.Status.PUBLISHED)
#         cart_items = [item for item in cart]
#         product_ids = [item["product_id"] for item in cart_items]
#
#         product_ids.append(product_id)
#
#
#
#         serializer = CartAddPostSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         # product_serializer = ProductSummarySerializer(product)
#
#
#         colors = serializer.validated_data['colors']
#         size = serializer.validated_data['size']
#         quantity = serializer.validated_data['quantity']
#         override = serializer.validated_data['override']
#         price = str(serializer.validated_data['price'])  # Decimal → str
#         final_price = str(serializer.validated_data.get('final_price', None))  # Decimal → str
#
#
#         cart.add(
#             product=product,
#             colors=colors,
#             size=size,
#             quantity=quantity,
#             override=override,
#             price=price,
#             final_price=final_price
#         )
#
#         return Response(product_ids, status=status.HTTP_201_CREATED)







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
    pagination_class = ProductPagination

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        discounted = validated_data.get('discounted', False)
        products = Product.objects.filter(available=True, status=Product.Status.PUBLISHED).annotate(
            final_price=ExpressionWrapper(
                F("price") - (F("price") * F("discount_percentage") / 100),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )

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

        search_query = validated_data.get("search")
        if search_query:
            vector = SearchVector('name', 'article', weight='A') + SearchVector('description', weight='B')
            query = SearchQuery(search_query)
            products = products.annotate(
                search=vector,
                rank=SearchRank(vector, query)
            ).filter(Q(search=query) | Q(name__icontains=search_query)).order_by('-rank')

        # Ստանում ենք փոխարժեքը middleware-ից
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))
        price_currency = getattr(request, 'currency_code')


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

        # 🔥 Ավելացնում ենք առաջարկվող ապրանքներ՝ Recommender-ի միջոցով
        # recommender = Recommender()
        # recommended_products = recommender.suggest_products_for(products[:5])  # Ընտրում ենք առաջին 5-ը ֆիլտրվածներից


        # user_id = request.user.id  # Օգտատիրոջ ID-ն
        # hybrid_recommended_products = hybrid_recommendation(user_id=user_id, product_id=products[0].id, top_n=5)



        user_id = request.user.id if request.user.is_authenticated else None
        if user_id:
            # Վերադարձնում է առավելագույնը len(products) id-եր, որոնք հարմար են:
            all_ids = list(products.values_list('id', flat=True))
            rec_ids = [p.id for p in hybrid_recommendation(user_id, top_n=len(all_ids))
                       if p.id in all_ids]
        else:
            rec_ids = []

        ordering_case = Case(
            *[When(pk=pid, then=pos) for pos, pid in enumerate(rec_ids)],
            default=len(rec_ids),
            output_field=IntegerField()
        )
        products = products.annotate(rec_order=ordering_case)

        # 2) Order by նոր դաշտով և fallback-ը՝ name–ով
        products = products.order_by('rec_order', 'name')

        paginator = self.pagination_class()
        paginated_products = paginator.paginate_queryset(products, request, view=self)

        # Սերիալիզացնում ենք արդյունքները
        serialized_products = ProductListSerializer(
            paginated_products,
            many=True,
            context={'request': request}
        ).data

        # serialized_recommended_products = ProductListSerializer(
        #     recommended_products,
        #     many=True,
        #     context={'request': request}
        # ).data
        # serialized_hybrid_recommended_products = ProductListSerializer(
        #     hybrid_recommended_products,
        #     many=True,
        #     context={'request': request}
        # ).data

        return Response(
            {
                "products": serialized_products,
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "has_next": paginator.page.has_next(),
                "has_previous": paginator.page.has_previous(),
            },
            status=status.HTTP_200_OK
        )


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

    def post(self, request):
        product_id = request.data.get('product_id')
        size_id = request.data.get('size_id', None)

        if not product_id:
            return Response(
                {'error': 'Product ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(Product, id=product_id)

        size = None
        price = None
        if size_id:
            size = get_object_or_404(SizePrice, id=size_id, product=product)
            price = size.price

        # Հեռացնել նախորդ նույն ապրանքի wishlist item-ները՝ այլ չափսերով
        Wishlist.objects.filter(user=request.user, product=product).exclude(size=size).delete()

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product,
            size=size
        )

        if not created:
            wishlist_item.delete()
            return Response({
                'message': 'Removed from wishlist',
                "id": product_id,
                "size_id": size_id,
                "liked": False,
                "wishlist_size_id": size_id
            }, status=status.HTTP_200_OK)

        if price is None:
            price = product.price

        wishlist_item.price = price
        wishlist_item.save()

        return Response({
            'message': 'Added to wishlist',
            "id": product_id,
            "size_id": size_id,
            "liked": True,
            "wishlist_size_id": size_id
        }, status=status.HTTP_201_CREATED)



class WishlistProductsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Ստանալ wishlist-ի ապրանքները, որոնք կապված են օգտատիրոջ հետ
        wishlist_items = Wishlist.objects.filter(user=request.user)

        # Ստանում ենք Wishlist-ի ապրանքները, որոնք կապված են օգտատիրոջ հետ
        products = [item.product for item in wishlist_items]

        # Սերիալիզատորով տվյալները ստանալ
        serializer = ProductListSerializer(products, many=True, context={'request': request})

        # Վերադարձնել պատասխանը
        return Response({"products": serializer.data}, status=status.HTTP_200_OK)


class ReviewView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


    def get_object(self, review_id, user):
        review = get_object_or_404(Review, id=review_id)
        if review.user != user:
            raise PermissionDenied("Դուք չեք կարող փոփոխել կամ ջնջել այս review-ը")
        return review

    def get(self, request, product_id, review_id=None):
        """Վերադարձնում է բոլոր review-ները կամ կոնկրետ review-ը"""
        if review_id:
            review = get_object_or_404(Review, id=review_id, product_id=product_id)
            serializer = ReviewSerializer(review)
        else:
            reviews = Review.objects.filter(product=product_id, status='AP')
            serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request, product_id, review_id=None):
        data = request.data.copy()
        data['product'] = product_id
        serializer = ReviewSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            review = serializer.save()
            review.send_notification()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, product_id, review_id):
        """Թարմացնում է օգտագործողի սեփական review-ը"""
        review = get_object_or_404(Review, id=review_id, product_id=product_id)

        if review.user != request.user:
            raise PermissionDenied("Դուք չեք կարող փոփոխել այս review-ը")

        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id, review_id):
        """Ջնջում է օգտագործողի սեփական review-ը"""
        review = get_object_or_404(Review, id=review_id, product_id=product_id)

        if review.user != request.user:
            raise PermissionDenied("Դուք չեք կարող ջնջել այս review-ը")

        review.delete()
        return Response({"message": "Review deleted successfully"}, status=status.HTTP_204_NO_CONTENT)








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




from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from decimal import Decimal
from .models import Currency  # Համոզվիր, որ ունես այս մոդելը

class SetCurrencyAPIView(APIView):
    """
    API որը թույլ է տալիս օգտատերերին ընտրել արժույթը և պահպանել session-ում կամ cache-ում:
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        price_currency = request.data.get('price_currency', 'USD')

        # Ստուգում ենք՝ արդյոք արժույթը առկա է մոդելում
        currency = get_object_or_404(Currency, code=price_currency)

        # Պահպանում ենք session-ում և cache-ում
        self._set_currency_in_session(request, price_currency)
        self._set_currency_in_cache(request, price_currency)

        return Response(
            {
                "message": f"Currency set to {price_currency}",
                "currency": price_currency,
                "exchange_rate": str(currency.exchange_rate)  # Կարող է պետք գալ frontend-ում
            },
            status=status.HTTP_200_OK
        )

    def _set_currency_in_session(self, request, currency_code):
        """Պահպանում է ընտրած արժույթը session-ում"""
        request.session['price_currency'] = currency_code

    def _set_currency_in_cache(self, request, currency_code):
        """Եթե օգտատերը authentication ունի, պահպանում ենք cache-ում"""
        if request.user.is_authenticated:
            cache.set(f"user_currency_{request.user.id}", currency_code, timeout=60 * 60 * 24)



class GetAvailableCurrenciesAPIView(APIView):
    """
    API որը վերադարձնում է առկա արժույթները և դրանց փոխարժեքները:
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        currencies = Currency.objects.all().values("code", "exchange_rate")
        return Response({"currencies": list(currencies)}, status=status.HTTP_200_OK)






class ProductHybridRecommendationView(APIView):
    permission_classes = (AllowAny,)


    def get(self, request, product_id, user_id):
        recommended_products = hybrid_recommendation(user_id=user_id, product_id=product_id, top_n=5)


        serialized_recommended_products = ProductListSerializer(
            recommended_products,
            many=True,
            context={'request': request}
        ).data

        return Response(
            {
                "recommended_products": serialized_recommended_products,
            },
            status=status.HTTP_200_OK
        )
