from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'price', 'quantity', 'total_cost']

class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True)
    total_cost = serializers.ReadOnlyField(source='get_total_cost_after_discount')

    class Meta:
        model = Order
        fields = ['id', 'first_name', 'last_name', 'email', 'address', 'postal_code',
                  'city', 'created', 'updated', 'paid', 'status', 'total_cost', 'items']