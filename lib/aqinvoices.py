import logging
import sys
import os

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.dates as dates_helper
import lib.mappings.currency as currency

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def process_data(data):
    result = {
        'invoicenumber': str(data['z77'][0][20:]).strip(),
        'booksellerid': mariadb.get_aqbasketgroup_by_aleph_rec_key(data['z68'][0])[0],
        'shipmentdate': dates_helper.process_aleph_date(data['z77'][15]),
        'billingdate': dates_helper.process_aleph_date(data['z77'][13]),
        'closedate': dates_helper.process_aleph_date(data['z77'][18]),
        'shipmentcost': currency.parse_value(data['z77'][8]),
        'shipmentcost_budgetid': mariadb.get_budget_by_code(data['z76'][0])[0]
    }

    return result


def split_join(query_result):
    result = {
        "z601": query_result[:18],
        "z68": query_result[18:74],
        "z77": query_result[74:104],
        "z76": query_result[104:]
    }
    return result


def start(credentials):

    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    data_cursor = oracle.get_open_z68_with_invoices()

    counter = 0
    for query_result in data_cursor:
        split = split_join(query_result)
        result = process_data(split)
        logger.debug(result)
        counter += 1

   # logger.debug('%s values' % counter)
    data_cursor.close()

    oracle.close_connection()


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
