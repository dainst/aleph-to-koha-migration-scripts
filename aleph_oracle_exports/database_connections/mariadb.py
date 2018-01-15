import logging
import MySQLdb

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_connection():
    return MySQLdb.connect(host="127.0.0.1", user="koha_zenon", passwd="zenon", db="koha_mapping_db", port=3307,
                           use_unicode=True, charset='utf8')