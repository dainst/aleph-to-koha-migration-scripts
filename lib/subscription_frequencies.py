import logging
import sys

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.z08 as z08_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


FREQUENCY_COUNTER = 1
FREQUENCY_RELEVANCE_COUNTER = {}

DESCRIPTION_MAPPING = {
    'year': 'Jahr',
    'month': 'Monat',
    'week': 'Woche',
    'day': 'Tag'
}


def create_description(unit, units_per_issue):
    global DESCRIPTION_MAPPING

    if units_per_issue == 1:
        if unit == 'year':
            return 'jährlich'
        elif unit == 'month':
            return 'monatlich'
        elif unit == 'week':
            return 'wöchentlich'
        elif unit == 'day':
            return 'täglich'
    else:
        if unit == 'year':
            return 'alle %i Jahre' % units_per_issue
        elif unit == 'month':
            return 'alle %i Monate' % units_per_issue
        elif unit == 'week':
            return 'alle %i Wochen' % units_per_issue
        elif unit == 'day':
            return 'alle %i Tage' % units_per_issue


def parse_frequencies(result_dict, data_row):
    global FREQUENCY_COUNTER
    global FREQUENCY_RELEVANCE_COUNTER

    unit = z08_helper.map_interval_type(data_row[14].strip())
    units_per_issue = data_row[13]
    if units_per_issue == 0:
        unit = z08_helper.map_interval_type(data_row[10].strip())
        units_per_issue = data_row[9]

    if units_per_issue == 0:
        logger.debug(data_row)

    description = create_description(unit, units_per_issue)

    result = {
        'id': FREQUENCY_COUNTER,
        'description': description,
        'unit': unit,
        'unitsperissue': units_per_issue,
        'issuesperunit': 1,
    }

    key = (unit, units_per_issue)

    if key not in result_dict:
        result_dict[key] = result
        FREQUENCY_COUNTER += 1

    if key not in FREQUENCY_RELEVANCE_COUNTER:
        FREQUENCY_RELEVANCE_COUNTER[key] = 1
    else:
        FREQUENCY_RELEVANCE_COUNTER[key] += 1

    return result_dict


def fetch_data(credentials):

    oracle.establish_connection(credentials)

    cursor = oracle.get_z08_data()
    frequencies = dict()
    for row in cursor:
        frequencies = parse_frequencies(frequencies, row)
    cursor.close()

    sorted_frequency_counter = sorted(FREQUENCY_RELEVANCE_COUNTER, key=FREQUENCY_RELEVANCE_COUNTER.get)
    display_order = len(sorted_frequency_counter)
    for idx in sorted_frequency_counter:
        # logger.debug('%i -- %s' %(FREQUENCY_COUNTER[idx], frequencies[idx]))
        frequencies[idx]['displayorder'] = display_order
        display_order -= 1

    return frequencies


def write_data(result_dict):
    logger.debug(result_dict)


def start(credentials):
    frequencies = fetch_data(credentials)
    write_data(frequencies)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
