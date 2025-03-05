from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .cart import Cart  # Ensure you have a Cart class handling session-based cart logic
from shop.models import Product
from .serializers import CartAddProductSerializer

class CartAddAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)

        serializer = CartAddProductSerializer(data=request.data)
        if serializer.is_valid():
            cd = serializer.validated_data

            cart.add(
                product=product,
                color=cd.get('color'),
                size=cd.get('size'),
                quantity=cd.get('quantity'),
                override_quantity=cd.get('override')
            )
            return Response({"message": "Product added to cart successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartRemoveAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)
        return Response({"message": "Product removed from cart successfully"}, status=status.HTTP_200_OK)


class CartDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cart = Cart(request)
        cart_items = []

        for item in cart:
            cart_items.append({
                "product": item["product"].id,
                "name": item["product"].name,
                "color": item.get("color"),
                "size": item.get("size"),
                "quantity": item["quantity"],
                "price": item["price"],
                "total_price": item["total_price"]
            })

        return Response({"cart": cart_items}, status=status.HTTP_200_OK)
