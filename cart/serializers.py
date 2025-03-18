from rest_framework import serializers
from decimal import Decimal

class CartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.SerializerMethodField()


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    # total_price = serializers.SerializerMethodField()
    # total_items = serializers.SerializerMethodField()
    # discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal(0))
    # shipping_cost = serializers.SerializerMethodField()
    # total_with_shipping = serializers.SerializerMethodField()






