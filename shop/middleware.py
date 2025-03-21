from decimal import Decimal
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from .models import Currency  # Համոզվիր, որ ունես այս մոդելը

class CurrencyMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Ստանում է արժույթը request-ից, session-ից կամ cache-ից և պահում request-ում:
        """

        # Նախ փորձում ենք ստանալ request query-ից (`?price_currency=AMD`)
        price_currency = request.GET.get('price_currency')

        # Եթե request-ում չկա, փորձում ենք session-ից
        if not price_currency:
            price_currency = request.session.get('price_currency')

        # Եթե session-ում չկա, փորձում ենք cache-ից (եթե օգտատերը authentication ունի)
        if not price_currency and request.user.is_authenticated:
            price_currency = cache.get(f"user_currency_{request.user.id}")

        # Եթե դեռ չկա, օգտագործում ենք 'AMD' որպես default
        if not price_currency:
            price_currency = 'AMD'

        # Պահում ենք request-ում
        request.currency_code = price_currency
        request.conversion_rate = self.get_conversion_rate(price_currency)

    def get_conversion_rate(self, currency_code):
        """
        Փորձում է ստանալ փոխարժեքը տվյալ արժույթի համար:
        """
        try:
            currency = Currency.objects.get(code=currency_code)
            return Decimal(currency.exchange_rate)
        except Currency.DoesNotExist:
            return Decimal(1.0)  # Եթե արժույթը չկա, վերադարձնում ենք 1.0 փոխարժեք