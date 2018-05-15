import logging
import sys
import os
import re
import pickle

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.mappings.library_keys as library_keys
import lib.oracle_helper.dates as dates_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

ALEPH_TO_KOHA_MAPPING = {}
ALEPH_TO_KOHA_MAPPING_PATH = script_dir + '/subscription_patterns_mapping.pickle'

'''
NUMBERPATTERNS
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `label` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `displayorder` int(11) DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci NOT NULL,
  `numberingmethod` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `label1` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `add1` int(11) DEFAULT NULL,
  `every1` int(11) DEFAULT NULL,
  `whenmorethan1` int(11) DEFAULT NULL,
  `setto1` int(11) DEFAULT NULL,
  `numbering1` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `label2` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `add2` int(11) DEFAULT NULL,
  `every2` int(11) DEFAULT NULL,
  `whenmorethan2` int(11) DEFAULT NULL,
  `setto2` int(11) DEFAULT NULL,
  `numbering2` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `label3` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `add3` int(11) DEFAULT NULL,
  `every3` int(11) DEFAULT NULL,
  `whenmorethan3` int(11) DEFAULT NULL,
  `setto3` int(11) DEFAULT NULL,
  `numbering3` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
'''

MAX_NUMBER_PATTERN_VALUE = 99999
UNHANDLED_PATTERNS = []

SINGLE_VARIABLE_PATTERN = re.compile('^(.*)\$(.)(.*)$')
TWO_VARIABLES_PATTERN = re.compile('^(.*)\$(.)(.*)\$(.)(.*)$')

ADDED_PATTERN_COUNTER = 1


def handle_two_variable_pattern(previous_results, data, mapping):
    global UNHANDLED_PATTERNS

    result = dict()

    aleph_pattern = data[2].upper()
    koha_pattern = None
    match = TWO_VARIABLES_PATTERN.match(aleph_pattern)
    first_variable_type = None
    second_variable_type = None

    # In Koha, the variables in the pattern are {X}, {Y}, {Z}
    # while in Aleph $Y denotes a year, $V a volume etc. So Koha is more generic. Also, if $Y is the "highest order"
    # variable, it has to be represented as {X}
    if match is not None:
        (first_variable_type, second_variable_type) = (match.group(2), match.group(4))
        if first_variable_type == 'Y':
            if second_variable_type == 'V':
                result['label'] = '%sJahr%sBand%s' % (match.group(1), match.group(3), match.group(5))
                result['label2'] = 'Band'
                # result['add2'] =
            result['label1'] = 'Band'
            result['add1'] = 1
            result['every1'] = data[9]
            result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE
            result['numberingmethod'] = koha_pattern

            koha_pattern = '%s{X}%s{Y}%s' % (match.group(1), match.group(3), match.group(5))
        elif second_variable_type == 'Y':
            koha_pattern = '%s{Y}%s{X}%s' % (match.group(1), match.group(3), match.group(5))
    else:
        UNHANDLED_PATTERNS.append(aleph_pattern)
        return previous_results

    result['numberingmethod'] = koha_pattern

    return previous_results


def handle_single_variable_pattern(parsed_data, data, mapping):
    global MAX_NUMBER_PATTERN_VALUE
    global UNHANDLED_PATTERNS
    global SINGLE_VARIABLE_PATTERN
    global ADDED_PATTERN_COUNTER

    aleph_pattern = data[2].upper()
    koha_pattern = None
    match = SINGLE_VARIABLE_PATTERN.match(aleph_pattern)

    result = dict()
    unique_frequencies = list(set([frequency[1] for frequency in mapping[data[0]]]))

    result['add1'] = 1
    result['every1'] = 1

    if match is not None:
        koha_pattern = '%s{X}%s' % (match.group(1), match.group(3))
        variable_type = match.group(2)
        if variable_type == 'Y':
            result['label'] = '%sJahr%s' % (match.group(1), match.group(3))
            result['label1'] = 'Jahr'
            if len(unique_frequencies) == 1 and unique_frequencies[0][0] == 'year' and unique_frequencies[0][1] == 1:
                result['add1'] = 1
                result['every1'] = 1
            elif len(unique_frequencies) == 1 and unique_frequencies[0][0] == 'year' and unique_frequencies[0][1] > 1:
                result['add1'] = unique_frequencies[0][1]
                result['every1'] = 1
            elif len(unique_frequencies) == 1 and unique_frequencies[0][0] == 'month':
                result['add1'] = 1
                result['every1'] = int(12 / unique_frequencies[0][1])
            else:
                logger.error('Unhandled case of unique_frequencies for dataset %s.' % data[0])
                logger.error(unique_frequencies)
                return parsed_data
        elif variable_type == 'V':
            result['label'] = '%sBand%s' % (match.group(1), match.group(3))
            result['label1'] = 'Band'
            result['add1'] = 1
            result['every1'] = 1
        else:
            UNHANDLED_PATTERNS.append(data[2])
            return parsed_data

    result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE
    result['numberingmethod'] = koha_pattern
    values = tuple(result.values())
    result['id'] = ADDED_PATTERN_COUNTER

    if values not in parsed_data:
        parsed_data[values] = result
        ADDED_PATTERN_COUNTER += 1

    ALEPH_TO_KOHA_MAPPING[data[0]] = values

    return parsed_data


def parse_numbering_pattern(previous_results, data, mapping):
    global UNHANDLED_PATTERNS

    aleph_pattern = data[2].upper()

    variable_count = sum(c == '$' for c in aleph_pattern)
    if variable_count > 2:
        if data[2] not in UNHANDLED_PATTERNS:
            UNHANDLED_PATTERNS.append(aleph_pattern)
        return previous_results
    elif variable_count == 2:
        return handle_two_variable_pattern(previous_results, data, mapping)
    else:
        return handle_single_variable_pattern(previous_results, data, mapping)


def fetch_data(credentials):

    oracle.establish_connection(credentials)

    cursor = oracle.get_z08_data()
    numbering_patterns_data = dict()

    with open(script_dir + '/subscription_frequencies_mapping.pickle', 'rb') as mapping_file:
        mapping = pickle.load(mapping_file)
        for row in cursor:
            numbering_patterns_data = parse_numbering_pattern(numbering_patterns_data, row, mapping)

    cursor.close()

    for key in numbering_patterns_data:
        logger.debug(numbering_patterns_data[key])

    logger.warning('Unhandled patterns: ')
    for pattern in UNHANDLED_PATTERNS:
        logger.warning(pattern)

    logger.debug('Todo')


def start(credentials):
    global ALEPH_TO_KOHA_MAPPING
    global ALEPH_TO_KOHA_MAPPING_PATH

    fetch_data(credentials)

    with open(ALEPH_TO_KOHA_MAPPING_PATH, 'wb') as mapping_file:
        pickle.dump(ALEPH_TO_KOHA_MAPPING, mapping_file)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
