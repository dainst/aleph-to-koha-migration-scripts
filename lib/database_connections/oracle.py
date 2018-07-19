import logging
import cx_Oracle

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config = {
    'user': 'dai50',
    'password': 'DAI50',
    'dsn': '195.37.175.36/aleph23',
    'encoding': 'UTF-8',
    'nencoding': 'UTF-8'
}

connection = None

CLOSED = 'CLS'
VENDOR_CANCELLED = 'VC '
LIBRARY_CANCELLED = 'CNB'


def establish_connection(credentials):
    global connection

    connection = cx_Oracle.connect(credentials, encoding='UTF-8', nencoding='UTF-8')


def open_connection():
    global connection

    if connection is None:
        try:
            logger.debug("Trying to connect to OracleDB ...")
            connection = cx_Oracle.connect(**config)
            logger.debug("Connection to OracleDB established: %s", connection)
            return connection
        except cx_Oracle.Error as err:
            logger.error(err)
            raise Exception
        except cx_Oracle.Warning as warn:
            logger.warning(warn)
            raise Exception
    else:
        logger.debug('Connection to OracleDB already established!\n')


def close_connection():
    global connection

    if connection is not None:
        connection.close()
        logger.debug("Connection to OracleDB closed.\n")
    else:
        logger.debug("Connection to OracleDB was already closed!\n")

    connection = None


def get_cursor():
    global connection

    return connection.cursor()


def get_z30():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z30')


def get_z30_by_order_number(aleph_order_number):
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z30 WHERE Z30_ORDER_NUMBER=:1', (aleph_order_number+'%',))


def get_z30_with_order_number():
    global connection
    cur = connection.cursor()

    return cur.execute('SELECT * FROM Z30 WHERE Z30_ORDER_NUMBER IS NOT NULL')


def get_item_price_list():
    global connection
    statement = """
        SELECT
            TRIM(Z30_BARCODE) AS BARCODE_Z30,
            TO_CHAR((
                SELECT Z82_RATIO / 1000000 * Z75_I_TOTAL_AMOUNT / 100 / Z68_NO_UNITS
                FROM Z82
                WHERE
                    Z82_DATE <= Z68_ORDER_STATUS_DATE_X AND
                    Z82_CURRENCY_NAME = Z68_E_CURRENCY
                ORDER BY Z82_DATE DESC
                FETCH FIRST 1 ROW ONLY),
                'FM99999990.00') AS UNIT_TOTAL_PRICE
        FROM
            Z30,
            Z75,
            Z68,
            Z77
        WHERE
            (
            Z30_PRICE IS NULL OR
            REGEXP_LIKE(Z30_PRICE, '^(\D).*$') OR
            REGEXP_LIKE(RTRIM(Z30_PRICE), '^(.)(\D)$') OR
            REGEXP_LIKE(Z30_PRICE, '^(.*),(.*)$')
            ) AND
            Z30_REC_KEY_3 = Z75_REC_KEY_2 AND
            SUBSTR(Z75_REC_KEY_2, 1, 35) = Z77_REC_KEY AND
            Z68_REC_KEY = Z75_REC_KEY
        ORDER BY
            Z30_BARCODE"""
    result = None

    try:
        logger.debug("Fetching item price list ...")
        cursor = connection.cursor()
        cursor.execute(statement)
        result = cursor.fetchall()
        cursor.close()
        logger.debug('Item price list fetched.')
    except cx_Oracle.DatabaseError as ora_err:
        error, = ora_err.args
        logger.error("Oracle-Error-Code:", error.code)
        logger.error("Oracle-Error-Message:", error.message)
    except cx_Oracle.Error as err:
        logger.error(err)
    except cx_Oracle.Warning as warn:
        logger.warning(warn)

    return result


def get_z70():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z70')


def get_z70_by_rec_key(aleph_rec_key):
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z70 WHERE Z70_REC_KEY=:1', (aleph_rec_key,))


def get_z72():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z72')


def get_z68():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z68')


def get_open_z68():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z68 WHERE Z68_ORDER_STATUS!=:1 ' +
                       'AND Z68_ORDER_STATUS!=:2 ' +
                       'AND Z68_ORDER_STATUS!=:3 ', (CLOSED, VENDOR_CANCELLED, LIBRARY_CANCELLED))


def get_budgets_for_open_orders():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z601, Z68, Z76 WHERE Z68.Z68_REC_KEY = Z601.Z601_REC_KEY_3 ' +
                       'AND Z76.Z76_BUDGET_NUMBER = SUBSTRB(Z601.Z601_REC_KEY, 1, 50) ' +
                       'AND Z68.Z68_ORDER_STATUS!=:1 ' +
                       'AND Z68.Z68_ORDER_STATUS!=:2 ' +
                       'AND Z68.Z68_ORDER_STATUS!=:3 ' +
                       'AND Z601.Z601_TYPE=:4', (CLOSED, VENDOR_CANCELLED, LIBRARY_CANCELLED, 'ENC'))


def get_orders_to_budgets_mapping():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT DISTINCT Z68.Z68_REC_KEY, SUBSTRB(Z601.Z601_REC_KEY, 1, 50) FROM Z68, Z601 ' +
                       'WHERE Z68.Z68_REC_KEY = Z601.Z601_REC_KEY_3 AND Z601.Z601_TYPE=:1', ('ENC',))


def get_still_valid_budgets():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z76 WHERE Z76_VALID_DATE_TO > 20180000')


def get_budget_by_budget_number(bundget_number):
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z76 WHERE Z76_BUDGET_NUMBER=:1', (bundget_number,))


def get_open_z68_with_invoices():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z68, Z75, Z77 WHERE ' +
                       'Z68.Z68_REC_KEY = Z75.Z75_REC_KEY ' +
                       'AND Z77.Z77_REC_KEY = SUBSTRB(Z75.Z75_REC_KEY_2, 1, 35) ' +
                       'AND Z68.Z68_ORDER_STATUS!=:1 ' +
                       'AND Z68.Z68_ORDER_STATUS!=:2 ' +
                       'AND Z68.Z68_ORDER_STATUS!=:3', (CLOSED, VENDOR_CANCELLED, LIBRARY_CANCELLED))


def get_closed_z68():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z68 WHERE Z68_ORDER_STATUS=:1 ', (CLOSED,))


def get_sub_library_z602(key):
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT Z602_SUB_LIBRARY FROM Z602 WHERE Z602_REC_KEY=:1', (key,))


def get_orders_to_invoices_mapping():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT DISTINCT Z68.Z68_REC_KEY, Z601.Z601_REC_KEY_2 FROM Z68, Z601, Z75 ' +
                       'WHERE '
                       'Z68.Z68_REC_KEY = Z601.Z601_REC_KEY_3 '
                       'AND Z601.Z601_REC_KEY_2 = Z75.Z75_REC_KEY_2 '
                       'AND Z601.Z601_TYPE=:1', ('INV',))


def get_z00_data():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z00')


def get_z08_data():
    global connection
    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z08')


def get_subscription_data():
    global connection
    cur = connection.cursor()
    return cur.execute('SELECT Z16.*, Z601.Z601_REC_KEY, Z68.Z68_REC_KEY FROM Z16, Z601, Z68 ' +
                       'WHERE ' +
                       'Z16.Z16_ORDER_NUMBER = Z68.Z68_ORDER_NUMBER ' +
                       'AND Z68.Z68_REC_KEY = Z601.Z601_REC_KEY_3 ' +
                       'AND Z601.Z601_TYPE=:1', ('ENC',))


def get_subscription_to_order_mapping():
    global connection
    cur = connection.cursor()
    return cur.execute('SELECT Z16.Z16_REC_KEY, Z68.Z68_REC_KEY FROM Z16, Z68 ' +
                       'WHERE Z16.Z16_ORDER_NUMBER = Z68.Z68_ORDER_NUMBER')


def get_barcode_to_zenon_id_mapping():
    global connection
    cur = connection.cursor()
    return cur.execute('SELECT Z30.Z30_BARCODE, Z103.Z103_LKR_DOC_NUMBER FROM DAI01.Z103, DAI50.Z30 ' +
                       'WHERE ' +
                       'Z103.Z103_LKR_TYPE=:1 ' +
                       'AND SUBSTR(Z103.Z103_REC_KEY, 6, 9) = SUBSTR(Z30.Z30_REC_KEY, 0, 9)', ('ADM',))
