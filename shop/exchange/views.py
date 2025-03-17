from django.http import JsonResponse
from django.core.cache import cache
from exchange.tasks import fetch_and_store_exchange_rates

def exchange_rate_view(request, base_currency="USD"):
    """
    Ստուգում է cache-ում փոխարժեքները և վերադարձնում:
    Եթե չկան, ապա բեռնում է API-ից:
    """
    rates = cache.get(f"exchange_rates_{base_currency}")
    if not rates:
        fetch_and_store_exchange_rates.delay(base_currency)  # Եթե չկան, սկսում է բեռնումը
        return JsonResponse({"message": "Fetching exchange rates, try again later."}, status=202)

    return JsonResponse({"base_currency": base_currency, "exchange_rates": rates})