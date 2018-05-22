import logging
import sys
import os
import pickle

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.z08 as z08_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/029000_subscription_frequencies_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/subscription_frequencies_data_import.sql'

ALEPH_TO_KOHA_MAPPING = {}
ALEPH_TO_KOHA_MAPPING_PATH = script_dir + '/../pickles/subscription_frequencies_mapping.pickle'

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


def parse_frequencies(result_dict, data_row, volume_or_issue):
    global ALEPH_TO_KOHA_MAPPING
    global FREQUENCY_COUNTER
    global FREQUENCY_RELEVANCE_COUNTER

    if volume_or_issue == 'volume':
        unit = z08_helper.map_interval_type(data_row[10].strip())
        units_per_issue = data_row[9]
    else:
        unit = z08_helper.map_interval_type(data_row[14].strip())
        units_per_issue = data_row[13]

    if unit == 'month' and units_per_issue % 12 == 0:
        unit = 'year'
        units_per_issue = int(units_per_issue / 12)

    description = create_description(unit, units_per_issue)

    result = {
        'id': FREQUENCY_COUNTER,
        'description': description,
        'unit': unit,
        'unitsperissue': units_per_issue,
        'issuesperunit': 1,
    }

    key = (unit, units_per_issue)

    if units_per_issue != 0:
        koha_key = result['id']
        if key not in result_dict:
            result_dict[key] = result
            FREQUENCY_COUNTER += 1
        else:
            koha_key = result_dict[key]['id']

        if data_row[0] in ALEPH_TO_KOHA_MAPPING \
                and (koha_key, key, volume_or_issue, description) not in ALEPH_TO_KOHA_MAPPING[data_row[0]]:
            ALEPH_TO_KOHA_MAPPING[data_row[0]].append((koha_key, key, volume_or_issue, description))
        else:
            ALEPH_TO_KOHA_MAPPING[data_row[0]] = [(koha_key, key, volume_or_issue, description)]

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
        frequencies = parse_frequencies(frequencies, row, 'issue')
        frequencies = parse_frequencies(frequencies, row, 'volume')
    cursor.close()

    sorted_frequency_counter = sorted(FREQUENCY_RELEVANCE_COUNTER, key=FREQUENCY_RELEVANCE_COUNTER.get)
    display_order = len(sorted_frequency_counter)
    for idx in sorted_frequency_counter:
        # logger.debug('%i -- %s' % (FREQUENCY_RELEVANCE_COUNTER[idx], frequencies[idx]))
        frequencies[idx]['displayorder'] = display_order
        display_order -= 1

    return frequencies


def generate_insert_statements(data_dict, database_columns):
    import_table_statement = 'INSERT INTO subscription_frequencies ('
    keys_len = len(database_columns)

    for idx, key in enumerate(database_columns):

        if idx == keys_len - 1:
            import_table_statement += key
        else:
            import_table_statement += key + ','

    import_table_statement += ')\nVALUES'

    counter = 0

    for aleph_key in data_dict:
        frequency = data_dict[aleph_key]
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


def write_data(result_dict):

    database_columns = ['id', 'description', 'displayorder', 'unit', 'unitsperissue', 'issuesperunit']

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        import_table_statement = \
            generate_insert_statements(result_dict, database_columns)

        import_file.write(import_table_statement)
        mapping_file.write(import_table_statement)
        cursor.execute(import_table_statement)

        mariadb.commit()
        cursor.close()


def start(credentials):
    frequencies = fetch_data(credentials)
    write_data(frequencies)

    with open(ALEPH_TO_KOHA_MAPPING_PATH, 'wb') as mapping_file:
        pickle.dump(ALEPH_TO_KOHA_MAPPING, mapping_file)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
