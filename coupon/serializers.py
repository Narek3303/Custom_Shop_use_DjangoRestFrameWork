from rest_framework import serializers
from .models import Coupon
from django.utils import timezone


class CouponApplySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50, label="Coupon Code")

    def validate_code(self, value):
        """
        Validates that the coupon code exists, is active, and is within the valid date range.
        """
        now = timezone.now()
        try:
            coupon = Coupon.objects.get(code__iexact=value)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code.")

        # Check if coupon is active and within the valid date range
        if not coupon.active:
            raise serializers.ValidationError("This coupon is no longer active.")

        if coupon.valid_from > now:
            raise serializers.ValidationError("This coupon is not valid yet.")

        if coupon.valid_to < now:
            raise serializers.ValidationError("This coupon has expired.")

        return coupon  # Returning the coupon object so we can use it in the view
