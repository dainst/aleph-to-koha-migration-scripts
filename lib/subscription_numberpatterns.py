import logging
import sys
import os
import re
import pickle

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.z08 as z08_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_logger = logging.getLogger(__name__ + '_file')
file_logger.setLevel(logging.INFO)

log_file_handler = logging.FileHandler('fehlerhafte_heft_zu_band_angaben.log')
log_file_handler.setLevel(logging.DEBUG)
file_logger.addHandler(log_file_handler)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/' \
                                       '030000_subscription_numberpatterns_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/subscription_numberpatterns_data_import.sql'

ALEPH_TO_KOHA_MAPPING = {}
ALEPH_TO_KOHA_MAPPING_PATH = script_dir + '/../pickles/subscription_patterns_mapping.pickle'


MAX_NUMBER_PATTERN_VALUE = 99999
UNHANDLED_PATTERNS = []

SINGLE_VARIABLE_PATTERN = re.compile(r'^(.*)\$(.)(.*)$')
TWO_VARIABLES_PATTERN = re.compile(r'^(.*)\$(.)(.*)\$(.)(.*)$')
THREE_VARIABLES_PATTERN = re.compile(r'^(.*)\$(.)(.*)\$(.)(.*)\$(.)(.*)$')

FREQUENCY_ALEPH_TO_KOHA_MAPPING_PATH = script_dir + '/../pickles/subscription_frequencies_mapping.pickle'
FREQUENCY_MAPPING = None

PATTERN_COUNTER = 1
PATTERN_RELEVANCE_COUNTER = {}


def log_unhandled_patterns(data, reason):
    global UNHANDLED_PATTERNS

    msg = 'Z08_REC_KEY: %s, pattern: "%s", 1 volume every %i %s, 1 issue every %i %s, %i issues per volume -- %s' \
          % (data[0], data[2],
             data[9], z08_helper.map_interval_type(data[10]),
             data[13], z08_helper.map_interval_type(data[14]),
             data[11], reason)

    UNHANDLED_PATTERNS.append(msg)


def calculate_year_variables(data):

    global FREQUENCY_MAPPING

    single_frequency = list(set([frequency[1] for frequency in FREQUENCY_MAPPING[data[0]]]))

    if len(single_frequency) != 1:
        issue_count = data[13]
        issue_type = data[14]

        volume_count = data[9]
        volume_type = data[10]

        issues_per_volume = data[11]
        force_issue_frequency = False
        if issue_type != volume_type:
            # If volume is one, let's suppose it was never changed from the default value
            if volume_count == 1 and issue_count != 0:
                force_issue_frequency = True
            elif issue_type == 'M' and volume_type == 'Y' and issue_count * issues_per_volume != volume_count * 12:

                file_logger.warning('Fehlerhafte Angaben zu Erscheinungszyklus von %s:' % data[0])
                file_logger.warning('Heft erscheint %i alle %s, Band erscheint %i alle %s.'
                                  % (issue_count, issue_type, volume_count, volume_type))
                file_logger.warning('Zusätzliche Angabe "Hefte pro Band": %i\n' % issues_per_volume)
                return None

        if '$I' in data[2].upper() or force_issue_frequency:
            relevant_frequency = [frequency[1] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'issue']
        else:
            relevant_frequency = [frequency[1] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'volume']

        label = 'Jahr'
        if relevant_frequency[0][0] == 'year' and relevant_frequency[0][1] == 1:
            add = 1
            every = 1
        elif relevant_frequency[0][0] == 'year' and relevant_frequency[0][1] > 1:
            add = relevant_frequency[0][1]
            every = 1
        elif relevant_frequency[0][0] == 'month':
            add = 1
            every = int(12 / relevant_frequency[0][1])
        elif relevant_frequency[0][0] == 'week':
            add = 1
            every = int(52 / relevant_frequency[0][1])
        else:
            return None

    else:
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

    issue_count = data[13]
    issue_type = data[14]

    volume_count = data[9]
    volume_type = data[10]

    issues_per_volume = data[11]

    label = 'Band'
    if '$Y' in data[2].upper() and '$I' not in data[2].upper():
        # aleph volume frequency is the relevant one
        if volume_frequency[0][0] == 'year' and volume_frequency[0][1] >= 1:
            add = 1
            every = volume_frequency[0][1]
        elif volume_frequency[0][0] == 'month':
            add = 1
            every = 1
            whenmorethan = int(12 / volume_frequency[0][1])
        else:
            return None
    elif '$I' in data[2].upper():
        # aleph issue frequency is the relevant one
        if not issue_frequency:
            file_logger.warning('Fehlerhafte Angaben zu Erscheinungszyklus von %s:' % data[0])
            file_logger.warning('Heft erscheint %i alle %s, Band erscheint %i alle %s.'
                              % (issue_count, issue_type, volume_count, volume_type))
            file_logger.warning('Das zugehörige Muster %s erwartet aber eine Angabe zu issues.\n' % data[2])
            return None

        if issue_frequency[0][0] == 'year' and issue_frequency[0][1] >= 1:
            add = 1
            every = issues_per_volume
        elif issue_frequency[0][0] == 'month':
            add = 1
            every = issues_per_volume
            whenmorethan = int(12 / issue_frequency[0][1])
        elif issue_frequency[0][0] == 'week':
            add = 1
            every = issues_per_volume
            whenmorethan = int(52 / issue_frequency[0][1])
        else:
            return None
    else:
        return None

    return [label, add, every, whenmorethan, setto]


def calculate_issue_variables(data):
    global FREQUENCY_MAPPING
    global MAX_NUMBER_PATTERN_VALUE

    whenmorethan = MAX_NUMBER_PATTERN_VALUE
    setto = 1
    issue_frequency = [frequency[1] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'issue']

    label = 'Heft'

    if issue_frequency[0][0] == 'year' and issue_frequency[0][1] >= 1:
        add = 1
        every = issue_frequency[0][1]
    elif issue_frequency[0][0] == 'month':
        add = 1
        every = 1
        whenmorethan = int(12 / issue_frequency[0][1])
    elif issue_frequency[0][0] == 'week':
        add = 1
        every = 1
        whenmorethan = int(52 / issue_frequency[0][1])
    else:
        return None

    return [label, add, every, whenmorethan, setto]


def handle_three_variables_pattern(parsed_data, data):
    global UNHANDLED_PATTERNS
    global FREQUENCY_MAPPING
    global PATTERN_COUNTER
    global PATTERN_RELEVANCE_COUNTER

    result = dict()

    if not ('$I' in data[2].upper() and '$V' in data[2].upper() and '$Y' in data[2].upper()):
        log_unhandled_patterns(data, 'unhandled case for three variables (unknown variable found)')
        return parsed_data

    match = THREE_VARIABLES_PATTERN.match(data[2].upper())
    if match is None:
        log_unhandled_patterns(data, 'unhandled case for three variables (pattern match failed)')
        return parsed_data

    first_variable = match.group(2)
    second_variable = match.group(4)
    third_variable = match.group(6)

    pattern = match.group(1)
    label = match.group(1)

    if first_variable == 'Y':
        pattern += '{X}'
        label += '{Jahr}'
    elif first_variable == 'V':
        pattern += '{Y}'
        label += '{Band}'
    elif first_variable == 'I':
        label += '{Heft}'
        pattern += '{Z}'

    pattern += match.group(3)

    if second_variable == 'Y':
        pattern += '{X}'
        label += '{Jahr}'
    elif second_variable == 'V':
        label += '{Band}'
        pattern += '{Y}'
    elif second_variable == 'I':
        label += '{Heft}'
        pattern += '{Z}'

    pattern += match.group(5)

    if third_variable == 'Y':
        pattern += '{X}'
        label += '{Jahr}'
    elif third_variable == 'V':
        label += '{Band}'
        pattern += '{Y}'
    elif third_variable == 'I':
        label += '{Heft}'
        pattern += '{Z}'

    pattern += match.group(7)
    result['numberingmethod'] = pattern

    year_variables = calculate_year_variables(data)
    if year_variables is None:
        log_unhandled_patterns(data, 'unhandled case for three variables (no valid year variables)')
        return parsed_data
    volume_variables = calculate_volume_variables(data)
    if volume_variables is None:
        log_unhandled_patterns(data, 'unhandled case for three variables (no valid volume variables)')
        return parsed_data
    issue_variables = calculate_issue_variables(data)
    if issue_variables is None:
        log_unhandled_patterns(data, 'unhandled case for three variables (no valid issue variables)')
        return parsed_data

    result['label1'] = year_variables[0]
    result['add1'] = year_variables[1]
    result['every1'] = year_variables[2]
    result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE

    result['label2'] = volume_variables[0]
    result['add2'] = volume_variables[1]
    result['every2'] = volume_variables[2]
    result['whenmorethan2'] = volume_variables[3]
    result['setto2'] = volume_variables[4]

    result['label3'] = issue_variables[0]
    result['add3'] = issue_variables[1]
    result['every3'] = issue_variables[2]
    result['whenmorethan3'] = issue_variables[3]
    result['setto3'] = issue_variables[4]

    description = [frequency[3] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'issue']
    issue_variables = calculate_issue_variables(data)
    if issue_variables is None:
        log_unhandled_patterns(data, 'unable to parse issue variables')
        return parsed_data
    result['description'] = description[0]
    result['label'] = '%s, %s' % (label, result['description'])

    values = tuple(result.values())
    result['id'] = PATTERN_COUNTER

    if values not in parsed_data:
        parsed_data[values] = result
        PATTERN_COUNTER += 1
        ALEPH_TO_KOHA_MAPPING[data[0]] = result
    else:
        ALEPH_TO_KOHA_MAPPING[data[0]] = parsed_data[values]

    if values in PATTERN_RELEVANCE_COUNTER:
        PATTERN_RELEVANCE_COUNTER[values] += 1
    else:
        PATTERN_RELEVANCE_COUNTER[values] = 1

    return parsed_data


def handle_two_variables_pattern(parsed_data, data):
    global UNHANDLED_PATTERNS
    global FREQUENCY_MAPPING
    global PATTERN_COUNTER
    global PATTERN_RELEVANCE_COUNTER

    result = dict()

    year_exists = '$Y' in data[2].upper()
    volume_exists = '$V' in data[2].upper()
    issue_exists = '$I' in data[2].upper()

    if not ((year_exists and volume_exists) or (year_exists and issue_exists) or (volume_exists and issue_exists)):
        log_unhandled_patterns(data, 'unhandled case for two variables (neither $Y and $I, nor $Y and $V)')
        return parsed_data

    match = TWO_VARIABLES_PATTERN.match(data[2].upper())
    if match is None:
        log_unhandled_patterns(data, 'unhandled case for two variables (pattern match failed)')
        return parsed_data

    # In Koha, the variables in the pattern are {X}, {Y}, {Z}
    # while in Aleph $Y denotes a year, $V a volume etc. So Koha is more generic. Also, if $Y is the "highest order"
    # variable, it has to be represented as {X}

    first_variable_type = match.group(2)
    second_variable_type = match.group(4)

    if year_exists and volume_exists:
        year_variables = calculate_year_variables(data)
        if year_variables is None:
            log_unhandled_patterns(data, 'unhandled case for two variables (no valid year variables)')
            return parsed_data

        # Always use {X} as year variable
        result['label1'] = year_variables[0]
        result['add1'] = year_variables[1]
        result['every1'] = year_variables[2]
        result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE

        description = [frequency[3] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'volume']
        volume_variables = calculate_volume_variables(data)
        if volume_variables is None:
            log_unhandled_patterns(data, 'unhandled case for two variables (no valid volume variables)')
            return parsed_data

        result['label2'] = volume_variables[0]
        result['add2'] = volume_variables[1]
        result['every2'] = volume_variables[2]
        result['whenmorethan2'] = volume_variables[3]
        result['setto2'] = volume_variables[4]
        result['description'] = description[0]

        if first_variable_type == 'V':
            result['label'] = '%s{Band}%s{Jahr}%s' % (match.group(1), match.group(3), match.group(5))
            koha_pattern = '%s{Y}%s{X}%s' % (match.group(1), match.group(3), match.group(5))
        elif second_variable_type == 'V':
            result['label'] = '%s{Jahr}%s{Band}%s' % (match.group(1), match.group(3), match.group(5))
            koha_pattern = '%s{X}%s{Y}%s' % (match.group(1), match.group(3), match.group(5))
        else:
            log_unhandled_patterns(data, 'unhandled case for two variables')
            return parsed_data

    elif year_exists and issue_exists:
        year_variables = calculate_year_variables(data)
        if year_variables is None:
            log_unhandled_patterns(data, 'unhandled case for two variables (no valid year variables)')
            return parsed_data

        # Always use {X} as year variable
        result['label1'] = year_variables[0]
        result['add1'] = year_variables[1]
        result['every1'] = year_variables[2]
        result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE
        description = [frequency[3] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'issue']
        issue_variables = calculate_issue_variables(data)
        if issue_variables is None:
            log_unhandled_patterns(data, 'unhandled case for two variables (no valid issue variables)')
            return parsed_data

        result['label2'] = issue_variables[0]
        result['add2'] = issue_variables[1]
        result['every2'] = issue_variables[2]
        result['whenmorethan2'] = issue_variables[3]
        result['setto2'] = issue_variables[4]
        result['description'] = description[0]

        if first_variable_type == 'I':
            result['label'] = '%s{Heft}%s{Jahr}%s' % (match.group(1), match.group(3), match.group(5))
            koha_pattern = '%s{Y}%s{X}%s' % (match.group(1), match.group(3), match.group(5))
        elif second_variable_type == 'I':
            result['label'] = '%s{Jahr}%s{Heft}%s' % (match.group(1), match.group(3), match.group(5))
            koha_pattern = '%s{X}%s{Y}%s' % (match.group(1), match.group(3), match.group(5))
        else:
            log_unhandled_patterns(data, 'unhandled case for two variables')
            return parsed_data

    elif issue_exists and volume_exists:
        volume_variables = calculate_volume_variables(data)
        if volume_variables is None:
            log_unhandled_patterns(data, 'unhandled case for two variables (no valid year variables)')
            return parsed_data

        description = [frequency[3] for frequency in FREQUENCY_MAPPING[data[0]] if frequency[2] == 'issue']

        result['label1'] = volume_variables[0]
        result['add1'] = volume_variables[1]
        result['every1'] = volume_variables[2]
        result['whenmorethan1'] = volume_variables[3]
        result['setto1'] = volume_variables[4]
        result['description'] = description[0]

        issue_variables = calculate_issue_variables(data)
        if issue_variables is None:
            log_unhandled_patterns(data, 'unhandled case for two variables (no valid issue variables)')
            return parsed_data

        result['label2'] = issue_variables[0]
        result['add2'] = issue_variables[1]
        result['every2'] = issue_variables[2]
        result['whenmorethan2'] = issue_variables[3]
        result['setto2'] = issue_variables[4]
        result['description'] = description[0]

        if first_variable_type == 'I':
            result['label'] = '%s{Heft}%s{Band}%s' % (match.group(1), match.group(3), match.group(5))
            koha_pattern = '%s{Y}%s{X}%s' % (match.group(1), match.group(3), match.group(5))
        elif second_variable_type == 'I':
            result['label'] = '%s{Band}%s{Heft}%s' % (match.group(1), match.group(3), match.group(5))
            koha_pattern = '%s{X}%s{Y}%s' % (match.group(1), match.group(3), match.group(5))
        else:
            log_unhandled_patterns(data, 'unhandled case for two variables')
            return parsed_data

    else:
        log_unhandled_patterns(data, 'unhandled case for two variables (neither Y+I nor Y+V)')
        return parsed_data

    result['numberingmethod'] = koha_pattern
    result['label'] += ', %s' % result['description']

    values = tuple(result.values())
    result['id'] = PATTERN_COUNTER
    if values not in parsed_data:
        parsed_data[values] = result
        PATTERN_COUNTER += 1
        ALEPH_TO_KOHA_MAPPING[data[0]] = result
    else:
        ALEPH_TO_KOHA_MAPPING[data[0]] = parsed_data[values]

    if values in PATTERN_RELEVANCE_COUNTER:
        PATTERN_RELEVANCE_COUNTER[values] += 1
    else:
        PATTERN_RELEVANCE_COUNTER[values] = 1

    return parsed_data


def handle_single_variable_pattern(parsed_data, data):
    global MAX_NUMBER_PATTERN_VALUE
    global UNHANDLED_PATTERNS
    global SINGLE_VARIABLE_PATTERN
    global PATTERN_COUNTER
    global PATTERN_RELEVANCE_COUNTER

    aleph_pattern = data[2].upper()
    match = SINGLE_VARIABLE_PATTERN.match(aleph_pattern)

    result = dict()

    if match is not None:
        koha_pattern = '%s{X}%s' % (match.group(1), match.group(3))
        variable_type = match.group(2)
        if variable_type == 'Y':
            year_variables = calculate_year_variables(data)
            if year_variables is None:
                log_unhandled_patterns(data)
                return parsed_data

            result['label'] = '%s{Jahr}%s' % (match.group(1), match.group(3))
            result['label1'] = year_variables[0]
            result['add1'] = year_variables[1]
            result['every1'] = year_variables[2]

        elif variable_type == 'V':
            result['label'] = '%s{Band}%s' % (match.group(1), match.group(3))
            result['label1'] = 'Band'
            result['add1'] = 1
            result['every1'] = 1
        else:
            log_unhandled_patterns(data, 'unhandled case for single variable (neither V nor Y)')
            return parsed_data
    else:
        log_unhandled_patterns(data, 'unhandled case for single variable (pattern match failed)')
        return parsed_data

    description = list(set([frequency[3] for frequency in FREQUENCY_MAPPING[data[0]]]))
    if len(description) != 1:
        log_unhandled_patterns(data, 'unhandled case for single variable (no frequency data)')
        return parsed_data

    result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE
    result['numberingmethod'] = koha_pattern
    result['description'] = description[0]
    result['label'] += ', %s' % result['description']

    values = tuple(result.values())

    result['id'] = PATTERN_COUNTER
    if values not in parsed_data:
        parsed_data[values] = result
        PATTERN_COUNTER += 1
        ALEPH_TO_KOHA_MAPPING[data[0]] = result
    else:
        ALEPH_TO_KOHA_MAPPING[data[0]] = parsed_data[values]

    if values in PATTERN_RELEVANCE_COUNTER:
        PATTERN_RELEVANCE_COUNTER[values] += 1
    else:
        PATTERN_RELEVANCE_COUNTER[values] = 1
    return parsed_data


def parse_numbering_pattern(parsed_data, data):
    global UNHANDLED_PATTERNS

    aleph_pattern = data[2].upper()

    variable_count = sum(char == '$' for char in aleph_pattern)
    if variable_count > 3:
        if data[2] not in UNHANDLED_PATTERNS:
            log_unhandled_patterns(data, 'more than 3 variables in pattern')
        return parsed_data
    elif variable_count == 3:
        return handle_three_variables_pattern(parsed_data, data)
    elif variable_count == 2:
        return handle_two_variables_pattern(parsed_data, data)
    else:
        return handle_single_variable_pattern(parsed_data, data)


def fetch_data(credentials):

    global FREQUENCY_MAPPING
    global FREQUENCY_ALEPH_TO_KOHA_MAPPING_PATH

    oracle.establish_connection(credentials)

    cursor = oracle.get_z08_data()
    numbering_patterns_data = dict()

    with open(FREQUENCY_ALEPH_TO_KOHA_MAPPING_PATH, 'rb') as mapping_file:
        FREQUENCY_MAPPING = pickle.load(mapping_file)
        for row in cursor:
            numbering_patterns_data = parse_numbering_pattern(numbering_patterns_data, row)

    cursor.close()

    logger.warning('Unhandled patterns: ')
    for pattern in UNHANDLED_PATTERNS:
        # if 'more than 3 variables in pattern' in pattern:
        #     continue
        # if 'unhandled case for three variables (unknown variable found)' in pattern:
        #     continue
        logger.warning(pattern)

    sorted_frequency_counter = sorted(PATTERN_RELEVANCE_COUNTER, key=PATTERN_RELEVANCE_COUNTER.get)
    display_order = len(sorted_frequency_counter)
    for idx in sorted_frequency_counter:
        # logger.debug('%i -- %s' % (FREQUENCY_RELEVANCE_COUNTER[idx], frequencies[idx]))
        numbering_patterns_data[idx]['displayorder'] = display_order
        display_order -= 1

    numbering_patterns_data = numbering_patterns_data.values()

    return numbering_patterns_data


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
