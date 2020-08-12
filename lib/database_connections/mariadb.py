import logging
import MySQLdb

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

config = {
    'host': '127.0.0.1',
    'user': 'koha_zenon',
    'passwd': 'zenon',
    'db': 'koha_mapping_db',
    'port': 3307,
    'use_unicode': True,
    'charset': 'utf8'
}

connection = None


def get_db_name():
    return 'koha_mapping_db'


def get_cursor():
    global connection

    return connection.cursor()


def establish_connection():
    global connection

    connection = MySQLdb.connect(host="127.0.0.1", user="koha_zenon", passwd="zenon", db=get_db_name(), port=3307,
                                 use_unicode=True, charset='utf8')


def open_mariadb_connection():
    global connection

    if connection is None:
        try:
            logger.debug("Trying to connect to MariaDB ...")
            connection = MySQLdb.connect(**config)
            logger.debug("Connection to MariaDB established: %s", connection)
            return connection
        except MySQLdb.Error as err:
            logger.error(err)
            raise Exception
        except MySQLdb.Warning as warn:
            logger.warning(warn)
            raise Exception
    else:
        logger.debug('Connection to MariaDB already established!\n')


def close_mariadb_connection():
    global connection

    if connection is not None:
        connection.close()
        logger.debug("Connection to MariaDB closed.\n")
    else:
        logger.debug("Connection to MariaDB was already closed!\n")


def commit():
    global connection

    connection.commit()


def get_aqbookseller_by_aleph_vendor_key(aleph_vendor_key):
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM aqbooksellers WHERE `ALEPH_VENDOR_CODE`="'+aleph_vendor_key+'";')
    result = cursor.fetchone()

    return result


def get_aleph_vendor_code_koha_aqbookseller_mapping():
    global connection
    result = None

    try:
        logger.debug("Fetching 'Aleph_Vendor_Code Koha_Aqbookseller' mapping ...")
        cursor = connection.cursor()
        cursor.execute("SELECT `ALEPH_VENDOR_CODE`, `NAME` FROM aqbooksellers;")
        result = cursor.fetchall()
        logger.debug('Mapping fetched.')
    except MySQLdb.Error as err:
        logger.error(err)
    except MySQLdb.Warning as warn:
        logger.warning(warn)

    return result


def get_koha_aqbookseller_name_by_aleph_vendor_key(aleph_vendor_key):
    global connection
    result = None

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT `NAME` FROM aqbooksellers WHERE `ALEPH_VENDOR_CODE`=%s;", aleph_vendor_key)
        result = cursor.fetchone()
    except MySQLdb.Error as err:
        logger.error(err)
    except MySQLdb.Warning as warn:
        logger.warning(warn)

    return result


def get_aqbaskets():
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM aqbasket;')
    result = cursor.fetchall()
    return result


def get_aqbasket_by_aleph_rec_key(aleph_rec_key):
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM aqbasket WHERE `ALEPH_Z68_REC_KEY`="' + aleph_rec_key + '";')
    result = cursor.fetchone()
    return result


def get_aqbasketgroups():
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM aqbasketgroups;')
    result = cursor.fetchall()
    return result


def get_aqbasketgroup_by_aleph_rec_key(aleph_rec_key):
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM aqbasketgroups WHERE `ALEPH_Z68_REC_KEY`="' + aleph_rec_key + '";')

    result = cursor.fetchone()

    return result


def get_budget_period_by_aleph_budget_number(aleph_budget_number):
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT `budget_period_id` FROM aqbudgetperiods WHERE `ALEPH_Z76_BUDGET_NUMBER`= "%s";'
                   % aleph_budget_number)

    return cursor.fetchone()


def get_budget_by_code(budget_code):
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM `aqbudgets` WHERE `budget_code`="%s";' % budget_code)

    result = cursor.fetchall()

    if len(result) != 1:
        logger.debug('Invalid number of budgets with code %s:' % budget_code)
        logger.debug(result)
        return None

    return result[0]


def get_recent_budget(first_id, second_id):
    global connection
    cursor = connection.cursor()
    cursor.execute('SELECT `aqbudgets`.*, `aqbudgetperiods`.`budget_period_enddate` FROM `aqbudgets`, `aqbudgetperiods` ' +
                   'WHERE `aqbudgets`.`budget_id`="%s" and `aqbudgets`.`budget_period_id` = `aqbudgetperiods`.`budget_period_id`;' % first_id)
    first_budget = cursor.fetchone()
    cursor.close()

    cursor = connection.cursor()
    cursor.execute('SELECT `aqbudgets`.*, `aqbudgetperiods`.`budget_period_enddate` FROM `aqbudgets`, `aqbudgetperiods` ' +
                   'WHERE `aqbudgets`.`budget_id`="%s" and `aqbudgets`.`budget_period_id` = `aqbudgetperiods`.`budget_period_id`;' % second_id)
    second_budget = cursor.fetchone()
    cursor.close()

    if first_budget[-1] > second_budget[-1]:
        return first_budget[:-1]
    else:
        return second_budget[:-1]


def get_invoices():
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM `aqinvoices`')

    result = cursor.fetchall()

    if len(result) == 0:
        return None

    return result


def get_invoice_by_aleph_rec_key(aleph_rec_key):
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT * FROM `aqinvoices` WHERE `ALEPH_Z68_REC_KEY`="%s";' % aleph_rec_key)

    result = cursor.fetchall()

    if len(result) == 0:
        return None

    return result


def get_koha_and_aleph_order_id_pairs():
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT `ordernumber`, `ALEPH_Z68_REC_KEY` FROM `aqorders`;')

    result = cursor.fetchall()

    return result


def get_item_barcode_and_itemnumber_pairs():
    global connection

    cursor = connection.cursor()
    cursor.execute('SELECT `barcode`, `itemnumber` FROM `items`;')

    result = cursor.fetchall()

    return result


def get_subscription_id_and_biblionumber_pairs():
    global connection

    cursor = connection.cursor()
    query = 'SELECT biblionumber, subscriptionid ' \
            'FROM subscription'
    cursor.execute(query)
    result = cursor.fetchall()
    return result


def get_orders_with_subscription_ids():
    global connection

    cursor = connection.cursor()
    query = 'SELECT ordernumber, subscriptionid, parent_ordernumber FROM aqorders ' \
            'WHERE subscriptionid IS NOT NULL ' \
            'ORDER BY subscriptionid, ordernumber;'

    cursor.execute(query)
    result = cursor.fetchall()
    return result


def get_standing_orders():
    global connection

    cursor = connection.cursor()
    query = 'SELECT aqorders.ordernumber, aqorders.basketno, aqorders.parent_ordernumber FROM aqorders, aqbasket ' \
            'WHERE aqbasket.basketno = aqorders.basketno AND aqbasket.is_standing = 1 ' \
            'ORDER BY aqorders.basketno, aqorders.ordernumber;'

    cursor.execute(query)
    result = cursor.fetchall()
    return result
