from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CouponApplySerializer


class CouponApplyView(APIView):
    def post(self, request):
        # Deserialize the input data
        serializer = CouponApplySerializer(data=request.data)

        if serializer.is_valid():
            coupon = serializer.validated_data['code']

            # Store the coupon ID in the session
            request.session['coupon_id'] = coupon.id

            # Send back the coupon details along with success message
            return Response({
                "message": "Coupon applied successfully!",
                "coupon_id": coupon.id,
                "discount": coupon.discount,
                "valid_from": coupon.valid_from,
                "valid_to": coupon.valid_to
            }, status=status.HTTP_200_OK)

        # Return error responses if validation fails
        return Response({
            "error": "Invalid coupon",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)