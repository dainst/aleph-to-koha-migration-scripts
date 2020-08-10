import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def evaluate_is_standing(aleph_order_type):
    aleph_order_type = aleph_order_type.strip()

    if aleph_order_type == 'O' or aleph_order_type == 'S':
        return 1

    return 0


def evaluate_is_subscription(aleph_order_type):
    aleph_order_type = aleph_order_type.strip()

    return aleph_order_type == 'S'
