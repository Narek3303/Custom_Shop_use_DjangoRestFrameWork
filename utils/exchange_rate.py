import requests
from shop.models import Currency
from celery import shared_task
from django.conf import settings

api_key = settings.EXCHANGE_RATE_API_KEY

@shared_task
def update_currency_exchange_rates(base_currency="USD"):
    # API վերբեռնում (օրինակ՝ Fixer API)
    url = f'https://api.exchangerate-api.com/{api_key}/latest/{base_currency}'
    response = requests.get(url)
    data = response.json()

    # Ստուգեք, արդյոք API-ից փոխանցված տվյալները ճիշտ են
    if response.status_code == 200 and 'rates' in data:
        for code, rate in data['rates'].items():
            # Փորձեք գտնել տվյալ արժույթը և թարմացնել նրա փոխարժեքը
            try:
                currency = Currency.objects.get(code=code)
                currency.exchange_rate = rate
                currency.save()
            except Currency.DoesNotExist:
                # Եթե արժույթը չկա, ստեղծեք նոր
                Currency.objects.create(code=code, name=code, exchange_rate=rate)