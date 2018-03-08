import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

STATUS_MAPPING = {
    'NEW': 'new',
    'WP ': 'new',
    'PS ': 'new',
    'WB ': 'new',
    'QSV': 'new',
    'CNB': 'cancelled',
    'DNB': 'ordered',
    'RSV': 'new',
    'SV ': 'ordered',
    'VC ': 'cancelled',
    'CLS': 'complete'
}


def map_aleph_key(aleph_key):
    if aleph_key not in STATUS_MAPPING:
        logger.warning("Unknown Aleph order status: " + aleph_key)
        return None

    return STATUS_MAPPING[aleph_key]


def is_open(aleph_key):
    order_status = map_aleph_key(aleph_key)
    if order_status != 'cancelled' and order_status != 'complete':
        return True
    else:
        return False
