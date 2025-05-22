from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from shop.models import Product, Color, Size
from django.shortcuts import get_object_or_404
from decimal import Decimal


from .models import Cart, CartItem
from .serializers import CartItemSerializer


class CartItemListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        cart_items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(cart_items, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)



# Helper function to get or create cart
def get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(user=user, status='open')
    return cart

class CartListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        cart = get_or_create_cart(request.user)



        serializer = CartSerializer(cart, context={'request': request} )
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

        # Փորձում ենք գտնել արդյոք նույն ապրանքը արդեն զամբյուղում կա
        existing_item = CartItem.objects.filter(cart=cart, product=product, size=size, color=color).first()

        if existing_item:
            # Եթե ապրանքը արդեն կա զամբյուղում, նորից չենք ավելացնում
            return Response(
                {"message": "Item already exists in cart", "id": product_id, "size_id": size_id, "color_id": color_id},
                status=status.HTTP_200_OK
            )

        # Եթե չկա, նոր CartItem ենք ստեղծում
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            size=size,
            color=color,
            quantity=quantity,
            price=price
        )

        cart.update_total_price()

        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))

        serializer = CartSerializer(cart, context={'request': request, 'conversion_rate': conversion_rate})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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

        # Ստուգում ենք size և color ID-ները
        size = Size.objects.get(id=size_id) if size_id else None
        color = Color.objects.get(id=color_id) if color_id else None

        # Փնտրում ենք համապատասխան CartItem-ները
        cart_items = CartItem.objects.filter(cart=cart, product=product, size=size, color=color)

        if not cart_items.exists():
            return Response({"detail": "Product with selected size and color not found in the cart."},
                            status=status.HTTP_404_NOT_FOUND)

        # Ջնջում ենք բոլոր համապատասխան CartItem-ները
        cart_items.delete()

        cart.refresh_from_db()  # Թարմացնում ենք զամբյուղի տվյալները

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateCartItemQuantityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        product_id = request.data.get("product_id")
        size_id = request.data.get("size_id")
        quantity = request.data.get("quantity")

        print(f"Received data: Product ID={product_id}, Size ID={size_id}, Quantity={quantity}")

        if not product_id:
            return Response(
                {"error": "product_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Վավերացնում ենք քանակը
        if quantity is not None:
            try:
                quantity = int(quantity)
                if quantity < 1 or quantity > 99:
                    return Response(
                        {"error": "Quantity must be between 1 and 99."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                return Response(
                    {"error": "Quantity must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"error": "Quantity is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Փնտրում ենք CartItem-ը ըստ օգտատիրոջ, ապրանքի և չափսի
        try:
            lookup = {
                "cart__user": user,
                "product_id": product_id,
            }
            if size_id:
                lookup["size_id"] = size_id

            cart_item = get_object_or_404(CartItem, **lookup)
        except Exception as e:
            print(f"Error fetching CartItem: {e}")
            return Response(
                {"error": "Could not find CartItem with given product_id and optional size_id."},
                status=status.HTTP_404_NOT_FOUND
            )
        print(f"Found CartItem: {cart_item}")

        # Թարմացնում ենք քանակը
        cart_item.update_quantity(quantity)


        # Թարմացնում ենք զամբյուղը
        cart_item.cart.refresh_from_db()
        cart_item.cart.save()

        serializer = CartSerializer(cart_item.cart, context={'request': request})
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
