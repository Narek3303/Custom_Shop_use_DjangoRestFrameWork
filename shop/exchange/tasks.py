import requests
from celery import shared_task
from shop.models import Currency
from django.conf import settings
import logging

# Set up logger
logger = logging.getLogger(__name__)

api_key = settings.EXCHANGE_RATE_API_KEY


@shared_task
def update_currency_exchange_rates():
    """
    Թարմացնում է արժույթի փոխարժեքները ExchangeRate API-ի միջոցով։
    """
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/USD'

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)

        data = response.json()

        if 'conversion_rates' in data:
            for code, rate in data['conversion_rates'].items():
                # Փորձեք գտնել տվյալ արժույթը
                try:
                    currency = Currency.objects.get(code=code)
                    currency.exchange_code = rate
                    currency.save()
                except Currency.DoesNotExist:
                    # Եթե արժույթը չկա, ստեղծեք նոր
                    Currency.objects.create(code=code, name=code, exchange_code=rate)
        else:
            logger.error("No conversion_rates found in the API response.")
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logger.error(f"Other error occurred: {err}")