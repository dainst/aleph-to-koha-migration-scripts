import logging
import re

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

PATTERN_CURRENCY_VALUE_DECIMAL = re.compile(r'^\d+\.\d*$')
PATTERN_CURRENCY_VALUE_LEADING_ZEROES = re.compile(r'[0]+(\d+)')
PATTERN_CURRENCY_VALUE_ONLY_DIGITS = re.compile(r'^\d+$')
PATTERN_CURRENCY_EURO = re.compile(r'(\d+\.\d+).*€')

# See http://confluence:8090/pages/viewpage.action?pageId=44859465

CURRENCY_MAPPING = {
    'AUD': 'AUD',
    'BGN': 'BGN',
    'CAD': 'CAD',
    'CHF': 'CHF',
    'CNY': 'CNY',
    'DKK': 'DKK',
    'EGP': 'EGP',
    'EUR': 'EUR',
    'GBP': 'GBP',
    'ILS': 'NIS',
    'JPY': 'JPY',
    'NOK': 'NOK',
    'RUB': 'RUB',
    'SEK': 'SEK',
    'TRY': 'TRY',
    'USD': 'USD'
}

# All conversions to Euros, same values as defined in Koha's "Currencies and exchange rates"
CURRENCY_CONVERSION_RATE = {
    'AUD': 0.62204,
    'BGN': 0.51129,
    'CAD': 0.68129,
    'CHF': 0.89813,
    'CNY': 0.12942,
    'DKK': 0.13399,
    'EGP': 0.05354,
    'GBP': 1.11572,
    'ILS': 0.24899,
    'JPY': 0.00821,
    'NOK': 0.10328,
    'RUB': 0.01398,
    'SEK': 0.09432,
    'TRY': 0.15521,
    'USD': 0.89118
}

DEPRECATED_CURRENCY_MAPPING = {
    'ATS': 'EUR',
    'BEF': 'EUR',
    'BGL': 'BGN',
    'CYP': 'EUR',
    'DEM': 'EUR',
    'ESP': 'EUR',
    'FIM': 'EUR',
    'FRF': 'EUR',
    'GRD': 'EUR',
    'IEP': 'EUR',
    'ITL': 'EUR',
    'NGL': 'EUR',
    'PTE': 'EUR',
    'TRL': 'TRY'
}

DEPRECATED_CURRENCY_CONVERSION_RATE = {
    'ATS': 1 / 13.7603,
    'BEF': 1 / 40.3399,
    'BGL': 1 / 1000,
    'CYP': 1 / 0.585274,
    'DEM': 1 / 1.95583,
    'ESP': 1 / 166.386,
    'FIM': 1 / 5.94573,
    'FRF': 1 / 6.55957,
    'GRD': 1 / 340.750,
    'IEP': 1 / 0.787564,
    'ITL': 1 / 1936.27,
    'NGL': 1 / 2.20371,
    'PTE': 1 / 200.482,
    # 'TRL': 1 / 1000000 # deactivated, results in too small values
}


def map_from_currency(aleph_currency, replace_deprecated):
    if aleph_currency is None:
        logger.warning("Trying to map currency that is 'None', setting to 'EUR'")
        return 'EUR'
    elif aleph_currency not in CURRENCY_MAPPING:
        if replace_deprecated:
            return map_from_deprecated_currency(aleph_currency)
        else:
            logger.warning("The currency code " + aleph_currency + " could not be mapped.")
            return None
    else:
        return CURRENCY_MAPPING[aleph_currency]


def map_from_deprecated_currency(aleph_currency):
    if aleph_currency is None:
        logger.warning("Trying to map currency that is 'None', setting to 'EUR'")
        return 'EUR'
    elif aleph_currency not in DEPRECATED_CURRENCY_MAPPING:
        logger.warning("The currency code " + aleph_currency + " could not be mapped.")
        return None
    else:
        return DEPRECATED_CURRENCY_MAPPING[aleph_currency]


def parse_value(aleph_value, aleph_currency, replace_deprecated):
    if aleph_value is None:
        return 0.0

    aleph_value = aleph_value.replace(',', '.').strip()
    match_decimal = re.search(PATTERN_CURRENCY_VALUE_DECIMAL, aleph_value)
    match_with_leading_zeroes = re.search(PATTERN_CURRENCY_VALUE_LEADING_ZEROES, aleph_value)
    match_digit = re.search(PATTERN_CURRENCY_VALUE_ONLY_DIGITS, aleph_value)
    match_euro = re.search(PATTERN_CURRENCY_EURO, aleph_value)

    value = 0.0
    if match_decimal:
        value = float(aleph_value)
    elif len(aleph_value) == 14 and match_with_leading_zeroes:
        value = float(aleph_value[0:-2] + '.' + aleph_value[-2:])
    elif match_digit:
        value = float(aleph_value)
    elif match_euro:
        value = float(match_euro.group(1))
    else:
        logger.warning('Unable to parse currency value:')
        logger.warning(aleph_value)

    if aleph_currency in CURRENCY_CONVERSION_RATE:
        value *= CURRENCY_CONVERSION_RATE[aleph_currency]

    if replace_deprecated and aleph_currency in DEPRECATED_CURRENCY_CONVERSION_RATE:
        value *= DEPRECATED_CURRENCY_CONVERSION_RATE[aleph_currency]

    return round(value, 2)
