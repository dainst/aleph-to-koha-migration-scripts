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


def map_from_currency(aleph_currency):
    if aleph_currency is None:
        return None
    elif aleph_currency not in CURRENCY_MAPPING:
        logger.warning("The currency code " + aleph_currency + " could not be mapped.")
        return None
    else:
        return CURRENCY_MAPPING[aleph_currency]