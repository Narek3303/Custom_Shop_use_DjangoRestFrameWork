from rest_framework import serializers
from .models import CartItem
from shop.models import Wishlist
from decimal import Decimal
from shop.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    product_detail = ProductListSerializer(source='product', read_only=True)
    total_price = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    currency_code = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_detail',
            'size',
            'color',
            'quantity',
            'price',
            'total_price',
            'product_image',
            'liked',
            'currency_code'
        ]

    def get_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք
        return obj.price * conversion_rate

    def get_total_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք
        return round(obj.price * obj.quantity * conversion_rate)

    def get_product_image(self, obj):
        return obj.get_product_image()

    def get_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            size_id = request.query_params.get('size_id')
            liked_items = Wishlist.objects.filter(user=request.user, product=obj.product)
            if size_id:
                liked_items = liked_items.filter(size__size_id=size_id)
            return liked_items.exists()
        return False

    def get_currency_code(self, obj):
        request = self.context.get('request')
        return obj.currency_code(request) if hasattr(obj, 'currency_code') else "USD"

    # create() method can be removed unless used directly in views



from rest_framework import serializers
from .models import Cart
from .serializers import CartItemSerializer
from decimal import Decimal

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    update_total_price = serializers.SerializerMethodField()


    class Meta:
        model = Cart
        fields = ['id', 'user', 'status', 'total_price', 'update_total_price', 'item_count', 'items']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))

        # Հաշվարկեք cart-ի ընդհանուր գինը ըստ բոլոր CartItem-ների
        total_price = sum(item['total_price'] for item in data['items'])
        data['total_price'] = round(total_price * conversion_rate, 2)
        return data

    def get_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք
        return obj.price * conversion_rate

    def get_total_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք
        return round(Decimal(obj.price) * Decimal(obj.quantity) * conversion_rate)

    def get_update_total_price(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))  # Middleware-ից վերցնում ենք
        return obj.update_total_price() * conversion_rate

    def get_currency_code(self, obj):
        request = self.context.get('request')
        return getattr(request, 'currency_code', 'USD')  # Default to AMD


