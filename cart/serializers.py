


# class CartAddPostSerializer(serializers.Serializer):
#     colors = serializers.CharField(max_length=20, required=True)
#     size = serializers.CharField(required=True, max_length=4)
#     quantity = serializers.IntegerField(min_value=1)
#     override = serializers.BooleanField(default=False)
#     price = serializers.DecimalField(max_digits=10, decimal_places=2)
#     final_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)



from rest_framework import serializers
from .models import Cart, CartItem
from shop.models import Product, Wishlist
from shop.models import Size, Color
from decimal import Decimal

class CartItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    currency_code = serializers.SerializerMethodField()





    class Meta:
        model = CartItem
        fields = ['id', 'product', 'size', 'color', 'quantity', 'price', 'total_price', 'product_image', 'liked', 'currency_code']


    def get_product_image(self, obj):
        return obj.get_product_image()

    def get_liked(self, obj):
        user = self.context['request'].user
        request = self.context.get('request')

        if request and hasattr(request, 'user') and request.user.is_authenticated:
            size_id = request.query_params.get('size_id')

            # Ստանում ենք Wishlist-ի բոլոր տարրերը, որոնք համապատասխանում են product-ին
            liked_items = Wishlist.objects.filter(user=user, product=obj.product)

            # Եթե size_id կա, ապա պետք է համեմատենք SizePrice-ի `size_id`-ի հետ
            if size_id:
                liked_items = liked_items.filter(size__size_id=size_id)

            return liked_items.exists()
        return False


    def create(self, validated_data):
        product = validated_data['product']
        size = validated_data.get('size', None)
        color = validated_data.get('color', None)
        quantity = validated_data['quantity']
        price = validated_data['price']

        # Հաշվարկում ենք `total_price`
        total_price = price * quantity

        # Ստեղծում ենք `CartItem`
        cart_item = CartItem.objects.create(
            product=product,
            size=size,
            color=color,
            quantity=quantity,
            price=price,
            total_price=total_price
        )
        cart_item.save()
        return cart_item

    def get_price(self, obj):
        request = self.context.get('request')
        if request:
            print("Conversion Rate:", getattr(request, 'conversion_rate', Decimal(1.0)))  # debug
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))
        return obj.price * conversion_rate

    def get_total_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))
        return obj.total_price * conversion_rate  # Փոխակերպված ընդհանուր գինը


    def get_currency_code(self, obj):
        request = self.context.get('request')
        return obj.currency_code(request)










class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'status', 'total_price', 'item_count', 'items']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))

        data['total_price'] = Decimal(data['total_price']) * conversion_rate
        return data
