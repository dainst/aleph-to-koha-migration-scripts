import logging
import cx_Oracle

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_connection(credentials):
    con = cx_Oracle.connect(credentials, encoding='UTF-8', nencoding='UTF-8')
    return con
