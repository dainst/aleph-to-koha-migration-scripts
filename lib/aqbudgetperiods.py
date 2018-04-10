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


def split_budget_data(data):
    result = {
        'z601': data[:18],
        'z68': data[18:74],
        'z76': data[74:]
    }
    return result


def parse_status(aleph_value):
    if aleph_value == 'AC':
        return 1
    else:
        return 0


def parse_data(results, data):
    budget_key = data['z76'][0].strip()
    if budget_key in results:
        return results

    current_result = {
        'budget_period_startdate': dates_helper.process_aleph_date(data['z76'][19]),
        'budget_period_enddate': dates_helper.process_aleph_date(data['z76'][20]),
        'budget_period_active': parse_status(data['z76'][14]),
        'budget_period_description': data['z76'][5],
        'budget_period_total': None,  # TODO: Check where the periods max value comes  from in aleph
        'budget_period_locked': None,  # TODO: Something to add here?
    }

    results[budget_key] = current_result
    return results


def fetch_data(credentials):
    oracle.establish_connection(credentials)

    results = dict()

    data_cursor = oracle.get_budgets_for_open_orders()
    for query_result in data_cursor:
        split = split_budget_data(query_result)
        results = parse_data(results, split)

    data_cursor.close()
    oracle.close_connection()

    return results


def write_results(data):
    logger.info('Todo')


def start(credentials):
    results = fetch_data(credentials)
    write_results(results)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
