# services.py
from decimal import Decimal

def get_shipping_cost(request, total_after_discount):
    price_currency = request.GET.get('price_currency', 'USD')  # Default to 'USD'

    free_shipping_thresholds = {
        "USD": Decimal(100),
        "AMD": Decimal(40000),
        "RUB": Decimal(10000)
    }

    if price_currency in free_shipping_thresholds and total_after_discount > free_shipping_thresholds[price_currency]:
        return Decimal(0)

    return Decimal(10)
