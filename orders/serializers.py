from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'first_name', 'last_name', 'email', 'address', 'postal_code',
            'city', 'created', 'updated', 'paid', 'coupon', 'discount', 'items'
        ]
        read_only_fields = ['id', 'created', 'updated', 'items']

    def create(self, validated_data):
        items_data = self.context['request'].data.get('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = self.context['request'].data.get('items')
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.address = validated_data.get('address', instance.address)
        instance.postal_code = validated_data.get('postal_code', instance.postal_code)
        instance.city = validated_data.get('city', instance.city)
        instance.discount = validated_data.get('discount', instance.discount)
        instance.save()

        # Update items
        for item_data in items_data:
            item = OrderItem.objects.get(id=item_data['id'])
            item.product = item_data['product']
            item.price = item_data['price']
            item.quantity = item_data['quantity']
            item.save()

        return instance
