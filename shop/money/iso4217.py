from django.utils.translation import gettext_lazy as _

class Currency:
    def __init__(self, iso_number, decimals, symbol, name):
        self.iso_number = iso_number
        self.decimals = decimals
        self.symbol = symbol
        self.name = name

    def __repr__(self):
        return f"<Currency {self.name} ({self.symbol})>"

CURRENCIES = {
    'AED': Currency('784', 2, 'د.إ', _('United Arab Emirates Dirham')),
    'AMD': Currency('051', 0, '֏', _("Armenian Dram")),  # Ավելացված AMD
    'AUD': Currency('036', 2, '$', _("Australian Dollar")),
    'BHD': Currency('048', 3, '.د.ب', _('Bahraini Dinar')),
    'BOB': Currency('068', 2, 'Bs', _('Boliviano')),
    'BRL': Currency('986', 2, 'R$', _("Brazilian Real")),
    'CAD': Currency('124', 2, 'C$', _("Canadian Dollar")),
    'CHF': Currency('756', 2, 'SFr.', _("Swiss Franc")),
    'CNY': Currency('156', 2, '¥', _("Chinese Yuan")),
    'CZK': Currency('203', 2, 'Kč', _("Czech Koruna")),
    'EUR': Currency('978', 2, '€', _("Euro")),
    'GBP': Currency('826', 2, '£', _("Pound Sterling")),
    'HKD': Currency('344', 2, 'HK$', _("Hong Kong Dollar")),
    'HRK': Currency('191', 2, 'kn', _("Croatian Kuna")),
    'HUF': Currency('348', 0, 'Ft', _("Hungarian Forint")),
    'ILS': Currency('376', 2, '₪', _("Israeli Sheqel")),
    'INR': Currency('356', 2, '₹', _("Indian Rupee")),
    'JPY': Currency('392', 0, '¥', _("Japanese Yen")),
    'KWD': Currency('414', 3, 'د.ك', _("Kuwaiti Dinar")),
    'OMR': Currency('512', 3, 'ر.ع.', _('Omani Rial')),
    'QAR': Currency('634', 2, 'ر.ق', _('Qatari Riyal')),
    'RUB': Currency('643', 2, '₽', _("Russian Ruble")),
    'SAR': Currency('682', 2, 'ر.س', _('Saudi Riyal')),
    'TND': Currency('788', 3, 'TND', _("Tunisian Dinar")),
    'UAH': Currency('980', 2, '₴', _("Ukrainian Hryvnia")),
    'USD': Currency('840', 2, '$', _("US Dollar")),
    'SEK': Currency('752', 2, 'kr', _("Swedish Kronor")),
    'ZAR': Currency('710', 2, 'R', _("South African Rand")),
}