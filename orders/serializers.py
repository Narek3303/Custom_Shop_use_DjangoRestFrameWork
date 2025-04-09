from datetime import timezone

from rest_framework import serializers
from .models import Order, OrderItem, ShippingMethod, ShippingAddress, Shipping
from decimal import Decimal




class AnalyticsSerializer(serializers.Serializer):
    sales_over_time = serializers.ListField(child=serializers.DictField())
    top_products = serializers.ListField(child=serializers.DictField())
    revenue_stats = serializers.DictField()
    order_status_stats = serializers.ListField(child=serializers.DictField())
    payment_method_stats = serializers.ListField(child=serializers.DictField())




class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.
    """
    product_name = serializers.CharField(source="product.name", read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "product_name", "quantity", "price", "total_price"]

    def get_total_price(self, obj):
        return obj.quantity * obj.price


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    tax = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    phone = serializers.CharField(source='user_profile.phone_number', read_only=True)
    address = serializers.CharField(source='user_profile.address', read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "user", "email", "phone", "address",
            "status", "subtotal", "discount", "tax", "total", "items", "created_at"
        ]
        read_only_fields = ["order_number", "total", "subtotal", "created_at"]

    def create(self, validated_data):
        """
        Override create to generate order number and calculate totals.
        """
        order = Order.objects.create(**validated_data)
        order.total = order.calculate_total()
        order.save()
        return order

    def update(self, instance, validated_data):
        """
        Override update to recalculate total if necessary.
        """
        instance = super().update(instance, validated_data)
        instance.total = instance.calculate_total()
        instance.save()
        return instance




class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'
        read_only_fields = ('order',)

class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = '__all__'

class ShippingSerializer(serializers.ModelSerializer):
    tracking_url = serializers.SerializerMethodField()
    shipping_method = ShippingMethodSerializer()

    class Meta:
        model = Shipping
        fields = '__all__'
        read_only_fields = ('order', 'status', 'shipped_at', 'delivered_at')

    def get_tracking_url(self, obj):
        if obj.tracking_number and obj.shipping_method:
            carrier = obj.shipping_method.carrier.lower()
            if carrier == 'fedex':
                return f"https://www.fedex.com/fedextrack/?trknbr={obj.tracking_number}"
            elif carrier == 'ups':
                return f"https://www.ups.com/track?tracknum={obj.tracking_number}"
            elif carrier == 'dhl':
                return f"https://www.dhl.com/en/express/tracking.html?AWB={obj.tracking_number}"
        return obj.tracking_url





class ShippingCalculatorSerializer(serializers.Serializer):
    """
    Serializer առաքման արժեքի հաշվարկման համար
    """
    country = serializers.CharField(max_length=2, required=True)
    city = serializers.CharField(max_length=100, required=True)
    postal_code = serializers.CharField(max_length=20, required=False)
    weight = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.01')
    )
    length = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.1')
    )
    width = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.1')
    )
    height = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.1')
    )
    is_residential = serializers.BooleanField(default=False)
    insurance_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=Decimal('0.00')
    )

    def validate(self, data):
        """
        Հավելյալ վալիդացիա չափերի համար
        """
        if data['length'] * data['width'] * data['height'] > 1000000:  # 1 մ³-ից մեծ չլինի
            raise serializers.ValidationError("Package volume is too large")
        return data


from rest_framework.response import Response
from rest_framework.views import APIView
from .shipping.integrations.fedex import FedExIntegration  # Կամ ձեր առաքման մատակարարի ինտեգրացիան


class ShippingCalculatorView(APIView):
    """
    Առաքման արժեքի հաշվարկման API վերջնակետ
    """

    def post(self, request):
        serializer = ShippingCalculatorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        # Օգտագործեք ձեր առաքման ինտեգրացիան (օրինակ՝ FedEx)
        fedex = FedExIntegration()
        rates = fedex.get_rates(
            origin={
                'postal_code': '0000',  # Ձեր պահեստի փոստային կոդը
                'country_code': 'AM'  # Ձեր երկրի կոդը
            },
            destination={
                'postal_code': data.get('postal_code', ''),
                'country_code': data['country'],
                'residential': data['is_residential']
            },
            package={
                'weight': float(data['weight']),
                'length': float(data['length']),
                'width': float(data['width']),
                'height': float(data['height'])
            }
        )

        if not rates:
            return Response(
                {"error": "Could not calculate shipping rates"},
                status=400
            )

        return Response({
            "rates": rates,
            "calculation_date": timezone.now().isoformat()
        })
