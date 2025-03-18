from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .cart import Cart
from shop.models import Product
from .serializers import CartSerializer
from rest_framework import permissions


class CartDetailAPIView(APIView):
    """
    Retrieve cart information, including all cart items, total price,
    discount, shipping cost, and item count.
    """
    # serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart = Cart(request)
        # Calculate total price, discount, shipping, etc.

        serializer = CartSerializer({
            'total_price': cart.get_total_price(),
            'total_items': len(cart),
            'discount': cart.get_discount(),
            'shipping_cost': cart.get_shipping_cost(),
            'total_with_shipping': cart.get_total_with_shipping(),
            'is_empty': cart.is_empty(),
            'get_items': cart.get_items(),
            'total_after_discount': cart.get_total_after_discount(),

            'items': [{
                'product_id': item['product'].id,
                'product_name': item['product'].name,
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['price'],
            } for item in cart],
        })
        return Response(serializer.data)






class CartRemoveAPIView(APIView):
    """
    Remove a product from the cart.
    """

    def post(self, request, product_id):
        cart = Cart(request)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        cart.remove(product)
        return Response({"message": "Product removed from cart successfully"}, status=status.HTTP_200_OK)


class CartClearAPIView(APIView):
    """
    Clear the cart.
    """

    def post(self, request):
        cart = Cart(request)
        cart.clear()
        return Response({"message": "Cart cleared successfully"}, status=status.HTTP_200_OK)


class CartUpdateAPIView(APIView):
    """
    Update quantity of a product in the cart.
    """

    def post(self, request, product_id):
        cart = Cart(request)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            quantity = int(request.data.get('quantity', 1))
            if quantity <= 0:
                return Response({"error": "Quantity must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid quantity value"}, status=status.HTTP_400_BAD_REQUEST)
        cart.add(product=product, quantity=quantity, override=True)

        return Response({"message": "Cart updated successfully"}, status=status.HTTP_200_OK)


class CartTotalPriceAPIView(APIView):
    """
    Get the total price of all items in the cart.
    """

    def get(self, request):
        cart = Cart(request)
        total_price = cart.get_total_price()
        total_with_shipping = cart.get_total_with_shipping()
        return Response({
            "total_price": total_price,
            "total_with_shipping": total_with_shipping,
        }, status=status.HTTP_200_OK)

