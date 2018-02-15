import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def evaluate_is_standing(aleph_order_type):
    aleph_order_type = aleph_order_type.strip()

    if aleph_order_type == 'O':
        return 1

    return 0
