from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .cart import Cart
from shop.models import Product
from .serializers import CartSerializer

class CartDetailAPIView(APIView):
    """
    Retrieve cart information, including all cart items, total price,
    discount, shipping cost, and item count.
    """

    def get(self, request):
        cart = Cart(request)
        # Calculate total price, discount, shipping, etc.
        serializer = CartSerializer({
            'total_price': cart.get_total_price(),
            'total_items': len(cart),
            'discount': cart.get_discount(),
            'shipping_cost': cart.get_shipping_cost(),
            'total_with_shipping': cart.get_total_with_shipping(),
            'items': [{
                'product_id': item['product'].id,
                'product_name': item['product'].name,
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['total_price'],
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
        return Response({"message": "Product removed from cart successfully"}, status=status.HTTP_204_NO_CONTENT)


class CartClearAPIView(APIView):
    """
    Clear the cart.
    """

    def post(self, request):
        cart = Cart(request)
        cart.clear()
        return Response({"message": "Cart cleared successfully"}, status=status.HTTP_204_NO_CONTENT)


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

        quantity = int(request.data.get('quantity', 1))
        cart.add(product=product, quantity=quantity, override_quantity=True)

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
            "total_price": str(total_price),
            "total_with_shipping": str(total_with_shipping),
        }, status=status.HTTP_200_OK)

