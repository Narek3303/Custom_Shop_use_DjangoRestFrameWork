from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class InventoryError(Exception):
    """Exception raised for inventory-related errors."""
    pass

class PaymentProcessingError(Exception):
    """Exception raised for errors in payment processing."""
    pass

class FraudDetectionError(Exception):
    """Exception raised for fraudulent order attempts."""
    pass




class OrderValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Order validation failed.')
    default_code = 'order_validation_error'

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        super().__init__(detail=detail, code=code)