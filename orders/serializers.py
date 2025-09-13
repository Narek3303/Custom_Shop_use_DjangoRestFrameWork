from django.utils import timezone
from rest_framework import serializers
from .models import Order, OrderItem
from decimal import Decimal
from cart.models import Cart, CartItem


class AnalyticsSerializer(serializers.Serializer):
    sales_over_time = serializers.ListField(child=serializers.DictField())
    top_products = serializers.ListField(child=serializers.DictField())
    revenue_stats = serializers.DictField()
    order_status_stats = serializers.ListField(child=serializers.DictField())
    payment_method_stats = serializers.ListField(child=serializers.DictField())



class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    first_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'quantity', 'price',
            'weight', 'size', 'color', 'total_price', 'first_image'
        ]
        read_only_fields = ['price', 'weight', 'total_price']


    def get_first_image(self, obj):
        return obj.product.get_first_image()


class OrderCreateItemSerializer(serializers.ModelSerializer):
    """For creating order items from input"""
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'size', 'color']


class MoneyField(serializers.DecimalField):

    def to_representation(self, value):
        return format(value, ".2f")

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    subtotal = MoneyField(max_digits=12, decimal_places=2)
    total = MoneyField(max_digits=12, decimal_places=2)
    items_count = serializers.SerializerMethodField()
    currency_code = serializers.SerializerMethodField()

    def get_items_count(self, obj):
        return obj.items.count()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_profile', 'email', 'phone', 'address',
            'status', 'status_display', 'payment_method', 'currency_code',
            'subtotal', 'discount', 'tax', 'shipping_cost', 'total',
            'tracking_number', 'shipped_at', 'delivered_at',
            'is_paid', 'notes', 'created_at', 'updated_at', 'items',
            'items_count'  # Հավելյալ դաշտ
        ]
        read_only_fields = [
            'order_number', 'subtotal', 'total',
            'created_at', 'updated_at', 'items_count'
        ]



    def get_currency_code(self, obj):
        request = self.context.get('request')
        return obj.currency_code(request)

    def get_total(self, obj):
        request = self.context.get('request')
        conversion_rate = getattr(request, 'conversion_rate', Decimal(1.0))
        return float(obj.total * conversion_rate)


from decimal import Decimal

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderCreateItemSerializer(many=True)
    currency_code = serializers.SerializerMethodField()


    class Meta:
        model = Order
        fields = [
            'email', 'phone', 'address', 'payment_method', 'currency_code',
            'discount', 'tax', 'shipping_cost', 'notes', 'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        user_profile = getattr(user, 'userprofile', None) if user else None

        # Առաջին հերթին ստեղծում ենք Order instance, բայց դեռ չենք save անում
        order = Order(
            user=user,
            user_profile=user_profile,
            **validated_data
        )

        order.save()

        # Ստեղծում ենք OrderItem-ները
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                price=item_data['product'].price,
                weight=item_data['product'].weight,
                size=item_data.get('size'),
                color=item_data.get('color')
            )

        # Հիմա հաշվում ենք գումարները
        order.subtotal = order.calculate_subtotal()
        order.total = order.calculate_total()
        order.save(update_fields=['subtotal', 'total'])



    def get_currency_code(self, obj):
        request = self.context.get('request')
        return obj.currency_code(request)
