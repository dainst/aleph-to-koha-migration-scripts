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

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/' \
                                       '030000_subscription_numberpatterns_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/subscription_numberpatterns_data_import.sql'


ALEPH_TO_KOHA_MAPPING = {}
ALEPH_TO_KOHA_MAPPING_PATH = script_dir + '/subscription_patterns_mapping.pickle'


MAX_NUMBER_PATTERN_VALUE = 99999
UNHANDLED_PATTERNS = []

SINGLE_VARIABLE_PATTERN = re.compile('^(.*)\$(.)(.*)$')
TWO_VARIABLES_PATTERN = re.compile('^(.*)\$(.)(.*)\$(.)(.*)$')

FREQUENCY_MAPPING = None


def calculate_year_variables(data):

    global FREQUENCY_MAPPING

    single_frequency = list(set([frequency[1] for frequency in FREQUENCY_MAPPING[data[0]]]))

    if len(single_frequency) != 1:
        return None

    label = 'Jahr'
    if single_frequency[0][0] == 'year' and single_frequency[0][1] == 1:
        add = 1
        every = 1
    elif single_frequency[0][0] == 'year' and single_frequency[0][1] > 1:
        add = single_frequency[0][1]
        every = 1
    elif single_frequency[0][0] == 'month':
        add = 1
        every = int(12 / single_frequency[0][1])
    else:
        return None

    return [label, add, every]


def calculate_volume_variables(data):
    global FREQUENCY_MAPPING
    global MAX_NUMBER_PATTERN_VALUE

    whenmorethan = MAX_NUMBER_PATTERN_VALUE
    setto = 1
    volume_frequency = [frequency[1] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'volume']
    issue_frequency = [frequency[1] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'issue']

    label = 'Band'
    if issue_frequency == [] or volume_frequency[0][0] == issue_frequency[0][0]:
        add = 1
        every = 1
    else:
        logger.debug('Unhandled case: volume and issue frequency not equal.')
        logger.debug(volume_frequency)
        logger.debug(issue_frequency)
        logger.debug(data)
        logger.debug(FREQUENCY_MAPPING[data[0]])
        return None

    return [label, add, every, whenmorethan, setto]


def handle_two_variable_pattern(previous_results, data):
    global UNHANDLED_PATTERNS
    global FREQUENCY_MAPPING

    result = dict()

    aleph_pattern = data[2].upper()
    match = TWO_VARIABLES_PATTERN.match(aleph_pattern)

    # In Koha, the variables in the pattern are {X}, {Y}, {Z}
    # while in Aleph $Y denotes a year, $V a volume etc. So Koha is more generic. Also, if $Y is the "highest order"
    # variable, it has to be represented as {X}
    if match is not None:
        (first_variable_type, second_variable_type) = (match.group(2), match.group(4))
        if first_variable_type == 'Y' or second_variable_type == 'Y':
            year_variables = calculate_year_variables(data)
            if year_variables is None:
                UNHANDLED_PATTERNS.append(data[2])
                return previous_results

            # Always use {X} as year variable
            result['label1'] = year_variables[0]
            result['add1'] = year_variables[1]
            result['every1'] = year_variables[2]
            result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE

            if first_variable_type == 'V' or second_variable_type == 'V':

                description = [frequency[3] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'volume']
                volume_variables = calculate_volume_variables(data)
                if volume_variables is None:
                    UNHANDLED_PATTERNS.append(data[2])
                    return previous_results

                result['label2'] = volume_variables[0]
                result['add2'] = volume_variables[1]
                result['every2'] = volume_variables[2]
                result['whenmorethan1'] = volume_variables[3]
                result['setto'] = volume_variables[4]
                result['description'] = description[0]

                if first_variable_type == 'V':
                    result['label'] = '%sBand%sJahr%s' % (match.group(1), match.group(3), match.group(5))
                    koha_pattern = '%s{Y}%s{X}%s' % (match.group(1), match.group(3), match.group(5))
                elif second_variable_type == 'V':
                    result['label'] = '%sJahr%sBand%s' % (match.group(1), match.group(3), match.group(5))
                    koha_pattern = '%s{X}%s{Y}%s' % (match.group(1), match.group(3), match.group(5))
                else:
                    UNHANDLED_PATTERNS.append(aleph_pattern)
                    return previous_results
            else:
                UNHANDLED_PATTERNS.append(aleph_pattern)
                return previous_results
        else:
            UNHANDLED_PATTERNS.append(aleph_pattern)
            return previous_results
    else:
        UNHANDLED_PATTERNS.append(aleph_pattern)
        return previous_results

    result['numberingmethod'] = koha_pattern

    values = tuple(result.values())

    if values not in previous_results:
        previous_results[values] = result

    ALEPH_TO_KOHA_MAPPING[data[0]] = values

    return previous_results


def handle_single_variable_pattern(parsed_data, data):
    global MAX_NUMBER_PATTERN_VALUE
    global UNHANDLED_PATTERNS
    global SINGLE_VARIABLE_PATTERN

    aleph_pattern = data[2].upper()
    match = SINGLE_VARIABLE_PATTERN.match(aleph_pattern)

    result = dict()

    if match is not None:
        koha_pattern = '%s{X}%s' % (match.group(1), match.group(3))
        variable_type = match.group(2)
        if variable_type == 'Y':
            year_variables = calculate_year_variables(data)
            if year_variables is None:
                UNHANDLED_PATTERNS.append(data[2])
                return parsed_data

            result['label'] = '%sJahr%s' % (match.group(1), match.group(3))
            result['label1'] = year_variables[0]
            result['add1'] = year_variables[1]
            result['every1'] = year_variables[2]

        elif variable_type == 'V':
            result['label'] = '%sBand%s' % (match.group(1), match.group(3))
            result['label1'] = 'Band'
            result['add1'] = 1
            result['every1'] = 1
        else:
            UNHANDLED_PATTERNS.append(data[2])
            return parsed_data
    else:
        UNHANDLED_PATTERNS.append(data[2])
        return parsed_data

    description = list(set([frequency[3] for frequency in FREQUENCY_MAPPING[data[0]]]))
    if len(description) != 1:
        UNHANDLED_PATTERNS.append(data[2])
        return parsed_data

    result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE
    result['numberingmethod'] = koha_pattern
    result['description'] = description[0]

    values = tuple(result.values())

    if values not in parsed_data:
        parsed_data[values] = result

    ALEPH_TO_KOHA_MAPPING[data[0]] = values
    return parsed_data


def parse_numbering_pattern(previous_results, data):
    global UNHANDLED_PATTERNS

    aleph_pattern = data[2].upper()

    variable_count = sum(char == '$' for char in aleph_pattern)
    if variable_count > 2:
        if data[2] not in UNHANDLED_PATTERNS:
            UNHANDLED_PATTERNS.append(aleph_pattern)
        return previous_results
    elif variable_count == 2:
        return handle_two_variable_pattern(previous_results, data)
    else:
        return handle_single_variable_pattern(previous_results, data)


def fetch_data(credentials):

    global FREQUENCY_MAPPING

    oracle.establish_connection(credentials)

    cursor = oracle.get_z08_data()
    numbering_patterns_data = dict()

    with open(script_dir + '/subscription_frequencies_mapping.pickle', 'rb') as mapping_file:
        FREQUENCY_MAPPING = pickle.load(mapping_file)
        for row in cursor:
            numbering_patterns_data = parse_numbering_pattern(numbering_patterns_data, row)

    cursor.close()

    logger.warning('Unhandled patterns: ')
    for pattern in UNHANDLED_PATTERNS:
        logger.warning(pattern)

    numbering_patterns_data = numbering_patterns_data.values()

    sorted_patterns_data = sorted(numbering_patterns_data,  key=lambda k: k['label'])

    final_patterns_data = []
    counter = 1
    for item in sorted_patterns_data:
        item['id'] = counter
        final_patterns_data.append(item)
        counter += 1
    return final_patterns_data


def generate_insert_statements(data_list, database_columns):
    import_table_statement = 'INSERT INTO subscription_numberpatterns ('
    keys_len = len(database_columns)

    for idx, key in enumerate(database_columns):

        if idx == keys_len - 1:
            import_table_statement += key
        else:
            import_table_statement += key + ','

    import_table_statement += ')\nVALUES'

    counter = 0

    for frequency in data_list:
        if counter != 0:
            import_table_statement += ','

        import_table_statement += '\n('

        for idx, key in enumerate(database_columns):
            if idx == keys_len - 1:
                if key in frequency and frequency[key] is not None:
                    import_table_statement += '"' + str(frequency[key]) + '"'
                else:
                    import_table_statement += 'NULL'
            else:
                if key in frequency and frequency[key] is not None:
                    import_table_statement += '"' + str(frequency[key]) + '",'
                else:
                    import_table_statement += 'NULL,'

        import_table_statement += ')'
        counter = counter + 1

    import_table_statement += ';\n'

    return import_table_statement


def write_data(data):
    database_columns = ['id', 'label', 'displayorder', 'description', 'numberingmethod',
                        'label1', 'add1', 'every1', 'whenmorethan1', 'setto1', 'numbering1',
                        'label2', 'add2', 'every2', 'whenmorethan2', 'setto2', 'numbering2',
                        'label3', 'add3', 'every3', 'whenmorethan3', 'setto3', 'numbering3']

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        import_table_statement = \
            generate_insert_statements(data, database_columns)

        import_file.write(import_table_statement)
        mapping_file.write(import_table_statement)
        cursor.execute(import_table_statement)

        mariadb.commit()
        cursor.close()


def start(credentials):
    global ALEPH_TO_KOHA_MAPPING
    global ALEPH_TO_KOHA_MAPPING_PATH

    data = fetch_data(credentials)
    write_data(data)

    with open(ALEPH_TO_KOHA_MAPPING_PATH, 'wb') as mapping_file:
        pickle.dump(ALEPH_TO_KOHA_MAPPING, mapping_file)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
