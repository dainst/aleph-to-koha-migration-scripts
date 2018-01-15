import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
