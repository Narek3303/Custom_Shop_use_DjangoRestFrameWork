from rest_framework import serializers


class CartAddProductSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
    override = serializers.BooleanField()
    color = serializers.CharField(max_length=30)
    size = serializers.CharField(max_length=7)
