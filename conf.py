class DefaultSettings:
    def _setting(self, name, default=None):
        from django.conf import settings
        return getattr(settings, name, default)


    @property
    def SHOP_DEFAULT_CURRENCY(self):
        """
        The default currency this shop is working with. The default is ``EUR``.

        .. note:: All model- and form input fields can be specified for any other currency, this
                  setting is only used if the supplied currency is missing.
        """
        return self._setting('SHOP_DEFAULT_CURRENCY', 'EUR')


    @property
    def SHOP_MONEY_FORMAT(self):
        """
        When rendering an amount of type Money, use this format.

        Possible placeholders are:

        * ``{symbol}``: This is replaced by €, $, £, etc.
        * ``{currency}``: This is replaced by Euro, US Dollar, Pound Sterling, etc.
        * ``{code}``: This is replaced by EUR, USD, GBP, etc.
        * ``{amount}``: The localized amount.
        * ``{minus}``: Only for negative amounts, where to put the ``-`` sign.

        For further information about formatting currency amounts, please refer to
        https://docs.microsoft.com/en-us/globalization/locale/currency-formatting
        """
        return self._setting('SHOP_MONEY_FORMAT', '{minus}{symbol} {amount}')

app_settings = DefaultSettings()