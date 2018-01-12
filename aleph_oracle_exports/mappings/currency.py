import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Siehe http://confluence:8090/pages/viewpage.action?pageId=44859465
# bzw. docker

CURRENCY_MAPPING = {
    'ILS': 'NIS'
}


def map_from_currency(aleph_currency):
    if aleph_currency not in CURRENCY_MAPPING:
        return aleph_currency
    else:
        return CURRENCY_MAPPING[aleph_currency]