from rest_framework import serializers
from decimal import Decimal

class CartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        return Decimal(obj['price']) * obj['quantity']

class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal(0))
    shipping_cost = serializers.SerializerMethodField()
    total_with_shipping = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        return sum(item['price'] * item['quantity'] for item in obj['items'])

    def get_total_items(self, obj):
        return sum(item['quantity'] for item in obj['items'])

    def get_shipping_cost(self, obj):
        total = self.get_total_price(obj)
        return Decimal(0) if total > 100 else Decimal(10)

    def get_total_with_shipping(self, obj):
        total = self.get_total_price(obj) - self.validated_data.get('discount', Decimal(0))
        return total + self.get_shipping_cost(obj)



