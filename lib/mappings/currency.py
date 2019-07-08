import logging
import re

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

PATTERN_CURRENCY_VALUE_DECIMAL = re.compile(r'^\d+\.\d*$')
PATTERN_CURRENCY_VALUE_LEADING_ZEROES = re.compile(r'[0]+(\d+)')
PATTERN_CURRENCY_VALUE_ONLY_DIGITS = re.compile(r'^\d+$')

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

    value = 0.0
    if match_decimal:
        value = float(aleph_value)
    elif len(aleph_value) == 14 and match_with_leading_zeroes:
        value = float(aleph_value[0:-2] + '.' + aleph_value[-2:])
    elif match_digit:
        value = float(aleph_value)
    else:
        logger.warning('Unable to parse currency value:')
        logger.warning(aleph_value)

    return round(value, 2)
