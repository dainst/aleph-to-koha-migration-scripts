import logging
import MySQLdb

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


connection = None


def get_db_name():
    return 'koha_mapping_db'


def get_use_statement():
    return 'USE ' + get_db_name() + ";\n\n"


def get_cursor():
    global connection

    return connection.cursor()


def establish_connection():
    global connection

    connection = MySQLdb.connect(host="127.0.0.1", user="koha_zenon", passwd="zenon", db=get_db_name(), port=3307,
                                 use_unicode=True, charset='utf8')


def commit():
    global connection

    connection.commit()


def get_aqbookseller_by_aleph_key(aleph_vendor_key):
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM aqbooksellers WHERE `ALEPH_VENDOR_KEY`="'+aleph_vendor_key+'";')
    result = cursor.fetchone()

    return result
