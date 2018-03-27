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

    if aleph_date is None:
        return None

    if type(aleph_date) == str:
        if aleph_date == '00000000':
            return None
        elif len(aleph_date) != 8:
            logger.error('Aleph date format error: %s', aleph_date)
            return None
        else:
            return "-".join([aleph_date[0:4], aleph_date[4:6], aleph_date[6:8]])
    elif type(aleph_date) == int:
        if aleph_date == 0:
            return None
        else:
            date_as_string = str(aleph_date)
            return "-".join([date_as_string[0:4], date_as_string[4:6], date_as_string[6:8]])
    else:
        logger.error('Aleph date format error: %s', str(aleph_date))
