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


def get_z70():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z70')


def get_z70_by_rec_key(aleph_rec_key):
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z70 WHERE `Z70_REC_KEY` = ' + aleph_rec_key)


def get_z72():
    global connection

    cur = connection.cursor()
    return cur.execute('SELECT * FROM Z72')
