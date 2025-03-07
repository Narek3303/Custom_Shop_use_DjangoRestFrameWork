from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .cart import Cart
from shop.models import Product
from .serializers import CartSerializer

class CartDetailAPIView(APIView):
    """
    Retrieve cart information, including all cart items, total price, and item count.
    """

    def get(self, request):
        cart = Cart(request)
        serializer = CartSerializer({
            'total_price': cart.get_total_price(),
            'total_items': len(cart),
            'items': [{
                'product_id': item['product'].id,
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['total_price'],
                'product_name': item['product'].name,
            } for item in cart],
        })
        return Response(serializer.data)


class CartAddAPIView(APIView):
    """
    Add a product to the cart.
    """

    def post(self, request, product_id):
        cart = Cart(request)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(request.data.get('quantity', 1))
        color = request.data.get('color', '')
        size = request.data.get('size', '')
        cart.add(product=product, color=color, size=size, quantity=quantity)

        return Response({"message": "Product added to cart successfully"}, status=status.HTTP_201_CREATED)


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
        return Response({"total_price": str(cart.get_total_price())}, status=status.HTTP_200_OK)
