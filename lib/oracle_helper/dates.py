import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def process_aleph_date(aleph_date):
    """
    Maps Aleph date strings to Koha date strings
    :param aleph_date: YYYYMMDD
    :return: koha_date: YYYY-MM-DD
    """

    if aleph_date == '00000000' or aleph_date == 0 or aleph_date is None:
        return None
    elif len(aleph_date) != 8:
        logger.error('Aleph date format error: %s', aleph_date)
        return None
    else:
        return "-".join([aleph_date[0:4], aleph_date[4:6], aleph_date[6:8]])
