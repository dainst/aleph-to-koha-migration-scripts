import logging
import sys
import os

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.mappings.library_keys as library_keys
import lib.oracle_helper.dates as dates_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

PERIOD_MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/013000_aqbudgetperiods_data_mapping.sql'
PERIOD_IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqbudgetperiods_data_import.sql'

BUDGET_MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/024000_aqbudgets_data_mapping.sql'
BUDGET_IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqbudgets_data_import.sql'

AQBUDGETPERIODS_DATA = dict()
AQBUDGET_DATA = dict()

COUNT_CREATED_PERIODS = 0


def split_budget_data_by_aleph_table(data):
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


def create_notes(data):
    notes = ''

    if data[15] is not None:
        notes += ', %s' % data[15]
    if data[16] is not None:
        notes += ', %s' % data[16]
    if data[17] is not None:
        notes += ', %s' % data[17]
    if data[18] is not None:
        notes += ', %s' % data[18]


def create_aqbudgetperiod_from_parent(data):

    data_cursor = oracle.get_budget_by_budget_number(data[1])
    oracle_result = data_cursor.fetchall()
    data_cursor.close()
    if len(oracle_result) > 1:
        logger.error('More than one parent budget:')
        logger.error(oracle_result)
        logger.error('For budget: %s' % data[0])
        return None

    parent = oracle_result[0]

    if parent[1] is not None and parent[1].strip() != '':
        logger.error('More than one ancestor for budget: "%s"' % data[0])
        logger.error('Parent: "%s"' % parent[0])
        logger.error('Parent\'s parent: "%s"' % parent[1])
        logger.error('Parent\'s parents are not supported!')
        return None

    return create_aqbudgetperiod(parent)


def create_aqbudgetperiod(data):
    global COUNT_CREATED_PERIODS
    global AQBUDGETPERIODS_DATA

    budget_key = data[0].strip()

    if budget_key in AQBUDGETPERIODS_DATA:
        return AQBUDGETPERIODS_DATA[budget_key]

    result = {
        'budget_period_id': COUNT_CREATED_PERIODS + 1,
        'budget_period_startdate': dates_helper.process_aleph_date(data[19]),
        'budget_period_enddate': dates_helper.process_aleph_date(data[20]),
        'budget_period_active': parse_status(data[14]),
        'budget_period_description': budget_key,
        'budget_period_total': None,  # TODO: Check where the periods max value comes  from in aleph
        'budget_period_locked': None,  # TODO: Something to add here?
    }

    COUNT_CREATED_PERIODS += 1
    AQBUDGETPERIODS_DATA[budget_key] = result

    return result


def create_aqbudget(data, aqbudgetperiod):
    global AQBUDGET_DATA

    budget_key = data[0].strip()

    if budget_key in AQBUDGET_DATA:
        return AQBUDGET_DATA[budget_key]

    result = {
        'budget_code': budget_key,
        'budget_name': data[5],
        'budget_amount': None,
        'budget_encumb': None,
        'budget_expend': None,
        'budget_notes': create_notes(data),
        'budget_period_id': aqbudgetperiod['budget_period_id']
    }

    cursor = oracle.get_sub_library_z602('Z76  %s' % data[0])
    oracle_result = cursor.fetchall()
    cursor.close()
    if len(oracle_result) != 1:
        logger.error('No valid  branch code for budget: %s' % data[0])
        logger.error(oracle_result)
    if len(oracle_result) == 1:
        branch_code = oracle_result[0][0]
        if branch_code is not None:
            koha_code = library_keys.map_aleph_key(branch_code)
            result['budget_branchcode'] = koha_code

            if koha_code is None:
                if result['budget_notes'] is None:
                    result['budget_notes'] = 'Sublibraries: ' + branch_code
                else:
                    result['budget_notes'] = result['budget_notes'] + ', Sublibraries: ' + branch_code

    AQBUDGET_DATA[budget_key] = result

    return result


def parse_data(data):

    has_parent = False
    if data['z76'][1] is not None and data['z76'][1].strip() != '':
        has_parent = True

    if has_parent:
        budget_period = create_aqbudgetperiod_from_parent(data['z76'])
    else:
        budget_period = create_aqbudgetperiod(data['z76'])

    create_aqbudget(data['z76'], budget_period)


def fetch_data(credentials):
    oracle.establish_connection(credentials)

    logger.info('Reading data from Oracle...')
    oracle.establish_connection(credentials)

    data_cursor = oracle.get_still_valid_budgets()
    logger.debug('Processing data for current budgets.')
    for query_result in data_cursor:
        parse_data({'z76': query_result})

    data_cursor.close()

    data_cursor = oracle.get_budgets_for_open_orders()
    logger.info('Processing data for budgets with open orders..')
    for query_result in data_cursor:
        data = split_budget_data_by_aleph_table(query_result)
        parse_data(data)

    data_cursor.close()

    oracle.close_connection()


def generate_period_import_statements():
    global AQBUDGETPERIODS_DATA

    mapping_statement = insert_statement = 'INSERT INTO aqbudgetperiods ('
    column_names = ['budget_period_id', 'budget_period_startdate', 'budget_period_enddate', 'budget_period_active',
                    'budget_period_description', 'budget_period_total', 'budget_period_locked']
    first_column = True
    for name in column_names:
        if not first_column:
            mapping_statement += ','
            insert_statement += ','
        first_column = False

        mapping_statement += name
        insert_statement += name

    mapping_statement += ',ALEPH_Z76_BUDGET_NUMBER)\nVALUES'
    insert_statement += ')\nVALUES'

    first_row = True
    for aleph_key in AQBUDGETPERIODS_DATA:
        period = AQBUDGETPERIODS_DATA[aleph_key]

        if not first_row:
            mapping_statement += ','
            insert_statement += ','
        first_row = False

        mapping_statement += '\n('
        insert_statement += '\n('

        first_column = True
        for name in column_names:
            if not first_column:
                mapping_statement += ','
                insert_statement += ','
            first_column = False
            if name in period and period[name] is not None:
                mapping_statement += '"%s"' % str(period[name])
                insert_statement += '"%s"' % str(period[name])
            else:
                mapping_statement += 'NULL'
                insert_statement += 'NULL'

        mapping_statement += ',"' + aleph_key + '")'
        insert_statement += ')'

    return mapping_statement, insert_statement


def generate_budget_import_statements():
    global AQBUDGET_DATA
    mapping_statement = insert_statement = 'INSERT INTO aqbudgets ('
    column_names = ['budget_parent_id', 'budget_code', 'budget_name', 'budget_branchcode', 'budget_amount',
                    'budget_encumb', 'budget_expend', 'budget_notes', 'budget_period_id']

    first_column = True
    for name in column_names:
        if not first_column:
            mapping_statement += ','
            insert_statement += ','
        first_column = False

        mapping_statement += name
        insert_statement += name

    mapping_statement += ')\nVALUES'
    insert_statement += ')\nVALUES'

    first_row = True
    for aleph_key in AQBUDGET_DATA:
        period = AQBUDGET_DATA[aleph_key]

        if not first_row:
            mapping_statement += ','
            insert_statement += ','
        first_row = False

        mapping_statement += '\n('
        insert_statement += '\n('

        first_column = True
        for name in column_names:
            if not first_column:
                mapping_statement += ','
                insert_statement += ','
            first_column = False
            if name in period and period[name] is not None:
                mapping_statement += '"%s"' % str(period[name])
                insert_statement += '"%s"' % str(period[name])
            else:
                mapping_statement += 'NULL'
                insert_statement += 'NULL'

        mapping_statement += ')'
        insert_statement += ')'

    return mapping_statement, insert_statement


def write_budget_data():
    global PERIOD_MAPPING_SQL_OUTPUT_PATH
    global PERIOD_IMPORT_SQL_OUTPUT_PATH
    global BUDGET_MAPPING_SQL_OUTPUT_PATH
    global BUDGET_IMPORT_SQL_OUTPUT_PATH

    mapping_statement, import_statement = generate_period_import_statements()

    with open(PERIOD_IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, \
            open(PERIOD_MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        import_file.write(import_statement)

        mapping_file.write(mapping_statement)
        cursor.execute(mapping_statement)

        mariadb.commit()
        cursor.close()

    mapping_statement, import_statement = generate_budget_import_statements()

    with open(BUDGET_IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, \
            open(BUDGET_MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        import_file.write(import_statement)

        mapping_file.write(mapping_statement)
        cursor.execute(mapping_statement)

        mariadb.commit()
        cursor.close()


def start(credentials):
    global AQBUDGETPERIODS_DATA
    global AQBUDGET_DATA

    mariadb.establish_connection()
    fetch_data(credentials)

    logger.debug('Period count: %i' % len(AQBUDGETPERIODS_DATA))
    logger.debug('Budget count: %i' % len(AQBUDGET_DATA))

    write_budget_data()


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
