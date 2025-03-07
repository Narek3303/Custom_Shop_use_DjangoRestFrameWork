from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializes OrderItem data."""
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    """Serializes Order data."""
    items = OrderItemSerializer(many=True, read_only=True)  # Nested serializer for order items
    total_cost_before_discount = serializers.DecimalField(
        source='get_total_cost_before_discount', max_digits=10, decimal_places=2, read_only=True
    )
    total_discount = serializers.DecimalField(
        source='get_discount', max_digits=10, decimal_places=2, read_only=True
    )
    total_cost = serializers.DecimalField(
        source='get_total_cost', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Order
        fields = [
            'id', 'first_name', 'last_name', 'email', 'address', 'postal_code', 'city',
            'created', 'updated', 'paid', 'stripe_id', 'coupon', 'discount',
            'total_cost_before_discount', 'total_discount', 'total_cost', 'items'
        ]
