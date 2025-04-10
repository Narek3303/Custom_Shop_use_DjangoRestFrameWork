class InventoryError(Exception):
    """Exception raised for inventory-related errors."""
    pass

class PaymentProcessingError(Exception):
    """Exception raised for errors in payment processing."""
    pass

class FraudDetectionError(Exception):
    """Exception raised for fraudulent order attempts."""
    pass
