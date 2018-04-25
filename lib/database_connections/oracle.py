import logging
import cx_Oracle

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

connection = None


def establish_connection(credentials):
    global connection

    connection = cx_Oracle.connect(credentials, encoding='UTF-8', nencoding='UTF-8')


def close_connection():
    global connection

    connection.close()


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
                       'AND Z68_ORDER_STATUS!=:3 ', ('CLS', 'VC ', 'CNB'))


def get_budgets_for_open_orders():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z601, Z68, Z76 WHERE Z68.Z68_REC_KEY = Z601.Z601_REC_KEY_3 ' +
                       'AND Z76.Z76_BUDGET_NUMBER = SUBSTR(Z601.Z601_REC_KEY, 1, 50) ' +
                       'AND Z68.Z68_ORDER_STATUS!=:1 ' +
                       'AND Z68.Z68_ORDER_STATUS!=:2 ' +
                       'AND Z68.Z68_ORDER_STATUS!=:3 ', ('CLS', 'VC ', 'CNB'))


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
    return cur.execute('SELECT * FROM Z601, Z68, Z77, Z76 WHERE Z68.Z68_REC_KEY = Z601.Z601_REC_KEY_3 ' +
                       'AND Z77.Z77_REC_KEY = SUBSTR(Z601.Z601_REC_KEY_2, 1, 35) ' +
                       'AND Z76.Z76_BUDGET_NUMBER = SUBSTR(Z601.Z601_REC_KEY, 1, 50) ' +
                       'AND Z68.Z68_ORDER_STATUS!=:1 ' +
                       'AND Z68.Z68_ORDER_STATUS!=:2 ' +
                       'AND Z68.Z68_ORDER_STATUS!=:3 ', ('CLS', 'VC ', 'CNB'))


def get_open_z68_monograph():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z68 WHERE Z68_ORDER_STATUS!=:1 ' +
                       'AND Z68_ORDER_STATUS!=:2 ' +
                       'AND Z68_ORDER_STATUS!=:3 ' +
                       'AND (Z68_ORDER_TYPE=:4 OR Z68_ORDER_TYPE=:5)', ('CLS', 'VC ', 'CNB', 'M', 'O'))


def get_open_z68_serials():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z68 WHERE Z68_ORDER_STATUS!=:1 ' +
                       'AND Z68_ORDER_STATUS!=:2 ' +
                       'AND Z68_ORDER_STATUS!=:3 ' +
                       'AND (Z68_ORDER_TYPE=:4)', ('CLS', 'VC ', 'CNB', 'S'))


def get_not_cancelled_z68():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z68 WHERE Z68_ORDER_STATUS!=:1 ' +
                       'AND Z68_ORDER_STATUS!=:2 ', ('VC ', 'CNB'))


def get_closed_z68():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z68 WHERE Z68_ORDER_STATUS=:1 ', ('CLS',))


def get_sub_library_z602(key):
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT Z602_SUB_LIBRARY FROM Z602 WHERE Z602_REC_KEY=:1', (key,))


def get_orders_to_budgets_mapping():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT DISTINCT Z68.Z68_REC_KEY, SUBSTR(Z601.Z601_REC_KEY, 1, 50) FROM Z68, Z601 ' +
                       'WHERE Z68.Z68_REC_KEY = Z601.Z601_REC_KEY_3 AND Z601.Z601_TYPE=:1', ('ENC',))


def get_z00_data():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z00')
