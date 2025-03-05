from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .cart import Cart
from shop.models import Product
from .serializers import CartAddProductSerializer


class CartAddAPIView(APIView):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)

        serializer = CartAddProductSerializer(data=request.data)
        if serializer.is_valid():
            cd = serializer.validated_data
            cart.add(

                product=product,
                quantity=cd['quantity'],
                override_quantity=cd['override']
            )
            return Response({"message": "Product added to cart successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartRemoveAPIView(APIView):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)
        return Response({"message": "Product removed from cart successfully"}, status=status.HTTP_200_OK)


class CartDetailAPIView(APIView):
    permission_classes = (AllowAny,)


    def get(self, request):
        cart = Cart(request)
        for item in cart:
            item['update_quantity_form'] = CartAddProductForm(
                initial={'quantity': item['quantity'], 'override': True}
            )
        return Response({'cart': cart})

