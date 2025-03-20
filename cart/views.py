from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from shop.models import Product, Color, Size
from django.shortcuts import get_object_or_404
from decimal import Decimal


# Helper function to get or create cart
def get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(user=user, status='open')
    return cart

class CartListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        cart = get_or_create_cart(request.user)
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))
        serializer = CartSerializer(cart, context={'request': request, 'conversion_rate': conversion_rate})
        return Response(serializer.data)

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Ավելացնում է ապրանք զամբյուղի մեջ `size`, `color`, `quantity`, `price`-ով։
        """
        cart, created = Cart.objects.get_or_create(user=request.user, status="open")
        product_id = request.data.get("product")
        size_id = request.data.get("size")
        color_id = request.data.get("color")
        quantity = int(request.data.get("quantity", 1))
        price = request.data.get("price")

        if not product_id or not price:
            return Response({"error": "Product and price are required"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)
        size = get_object_or_404(Size, id=size_id) if size_id else None
        color = get_object_or_404(Color, id=color_id) if color_id else None

        # Ստուգում ենք, արդյոք այդ նույն ապրանքը արդեն կա զամբյուղում
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            color=color,
            defaults={"quantity": quantity, "price": price},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        cart.update_total_price()

        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)


class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Ստանում ենք body-ից անհրաժեշտ տվյալները
        product_id = request.data.get('product_id')
        size_id = request.data.get('size')  # size ID-ն
        color_id = request.data.get('color')  # color ID-ն

        # Ստուգում ենք, որ ապրանքը կա
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        cart = get_or_create_cart(request.user)

        # Ստուգում ենք, թե եթե size կամ color ID-ն կա, ապա գտնում ենք համապատասխան մոդելները
        size = None
        color = None

        if size_id:
            size = Size.objects.get(id=size_id)  # Փոխարինեք Size մոդելով, եթե դա ձեր մոդելն է

        if color_id:
            color = Color.objects.get(id=color_id)  # Փոխարինեք Color մոդելով, եթե դա ձեր մոդելն է

        # Պայման՝ ստուգելու, թե արդյոք ապրանքը, սայզը և գույնը գոյություն ունեն զամբյուղում
        if not CartItem.objects.filter(cart=cart, product=product, size=size, color=color).exists():
            return Response({"detail": "Product with selected size and color not found in the cart."},
                            status=status.HTTP_404_NOT_FOUND)

        # Հեռացնում ենք ապրանքը՝ հաշվի առնելով size-ը և color-ը
        cart.remove_item(product, size=size, color=color)  # Օգտագործում ենք վերևում ուղղված remove_item մեթոդը
        cart.refresh_from_db()  # Թարմացնում ենք զամբյուղի տվյալները

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UpdateCartItemQuantityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, cart_item_id, *args, **kwargs):
        cart_item = CartItem.objects.get(id=cart_item_id)
        quantity = request.data.get('quantity')
        cart_item.update_quantity(quantity)  # Using the update_quantity method from your CartItem model
        cart_item.cart.refresh_from_db()  # Refresh to get updated total_price
        cart_item.cart.save()
        cart = cart_item.cart
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart = get_or_create_cart(request.user)
        cart.clear_cart()  # Using the clear_cart method from your Cart model
        cart.refresh_from_db()  # Refresh to get updated total_price
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CloseCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart = get_or_create_cart(request.user)
        if not cart.is_empty():
            cart.close()  # Using the close method from your Cart model
        cart.refresh_from_db()  # Refresh to get updated status and total_price
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
