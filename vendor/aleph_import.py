import sys
import logging
import cx_Oracle

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def connect_to_database(connection_credentials):
    con = cx_Oracle.connect(connection_credentials)
    logger.info('Connected...')

    cur = con.cursor()
    cur.execute('SELECT * FROM Z00 WHERE ROWNUM < 10')
    for result in cur:
        logger.info(result)
    cur.close()
    con.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.info("Please provide as argument:")
        logger.info("1) Connection info and credentials, pattern: '%USER%/%PASSWORD%@%IP%/%SID%'.")
        sys.exit()

    connect_to_database(sys.argv[1])

