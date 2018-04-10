import logging
import sys
import os

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.dates as dates_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/013000_aqbudgetperiods_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqbudgetperiods_data_import.sql'


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
    logger.info('Reading data from Oracle...')
    oracle.establish_connection(credentials)

    results = dict()

    data_cursor = oracle.get_budgets_for_open_orders()
    for query_result in data_cursor:
        split = split_budget_data(query_result)
        results = parse_data(results, split)

    data_cursor.close()
    oracle.close_connection()

    return results


def generate_insert_statements(data, columns_names):
    mapping_table_statement = import_table_statement = 'INSERT INTO aqbudgetperiods ('
    keys_len = len(columns_names)

    for idx, key in enumerate(columns_names):

        if idx == keys_len - 1:
            import_table_statement += key

            mapping_table_statement += key
            mapping_table_statement += ',ALEPH_Z76_BUDGET_NUMBER'
        else:
            import_table_statement += key + ','
            mapping_table_statement += key + ','

    import_table_statement += ')\nVALUES'
    mapping_table_statement += ')\nVALUES'

    counter = 0

    for aleph_key in data:
        basket = data[aleph_key]
        if counter != 0:
            import_table_statement += ','
            mapping_table_statement += ','

        import_table_statement += '\n('
        mapping_table_statement += '\n('

        for idx, key in enumerate(columns_names):
            if idx == keys_len - 1:

                if key in basket and basket[key] is not None:
                    import_table_statement += '"' + str(basket[key]) + '"'
                    mapping_table_statement += '"' + str(basket[key]) + '"'
                else:
                    import_table_statement += 'NULL'
                    mapping_table_statement += 'NULL'

                mapping_table_statement += ', "' + aleph_key + '"'
            else:

                if key in basket and basket[key] is not None:
                    import_table_statement += '"' + str(basket[key]) + '",'
                    mapping_table_statement += '"' + str(basket[key]) + '",'
                else:
                    import_table_statement += 'NULL,'
                    mapping_table_statement += 'NULL,'

        import_table_statement += ')'
        mapping_table_statement += ')'

        counter = counter + 1

    import_table_statement += ';\n'
    mapping_table_statement += ';\n'

    return [import_table_statement, mapping_table_statement]


def write_results(data):
    logger.info('Writing data to file and mapping database.')

    database_columns = [
        'budget_period_startdate', 'budget_period_enddate', 'budget_period_active', 'budget_period_description',
        'budget_period_total', 'budget_period_locked', 'sort1_authcat', 'sort2_authcat'
    ]

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        [import_table_statement, mapping_table_statement] = \
            generate_insert_statements(data, database_columns)

        import_file.write(import_table_statement)

        mapping_file.write(mapping_table_statement)
        cursor.execute(mapping_table_statement)

        mariadb.commit()
        cursor.close()


def start(credentials):
    results = fetch_data(credentials)
    write_results(results)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
