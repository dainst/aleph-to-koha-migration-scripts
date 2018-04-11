import logging
import sys
import os

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.mappings.library_keys as library_keys

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/024000_aqbudgets_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqbudgets_data_import.sql'


def split_budget_data(data):
    result = {
        'z601': data[:18],
        'z68': data[18:74],
        'z76': data[74:]
    }
    return result


# Not implemented:
#  `budget_owner_id` int(11) DEFAULT NULL,
#  `budget_permission` int(1) DEFAULT 0,


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


def create_koha_data(data, parent_data):
    result = {
        'budget_code': data[0],
        'budget_name': data[5],
        'budget_amount': None,
        'budget_encumb': None,
        'budget_expend': None,
        'budget_notes': create_notes(data)
    }

    if parent_data is not None:
        result['parent_budget_code'] = parent_data['budget_code'].strip()

    budget_id_query = mariadb.get_budget_period_by_aleph_budget_number(data[0].strip())
    if budget_id_query is not None:
        result['budget_period_id'] = budget_id_query[0]

    cursor = oracle.get_sub_library_z602('Z76  %s' % data[0])
    oracle_result = cursor.fetchall()
    cursor.close()
    if len(oracle_result) != 1:
        logger.error('No valid  branch code for budget: %s' % data[0])
        logger.error(oracle_result)
    if len(oracle_result) == 1:
        branch_code = oracle_result[0][0]
        if branch_code is not None:
            result['budget_branchcode'] = library_keys.map_aleph_key(branch_code)
    return result


def exists_already_in_results(results, item, depths):
    index = 0
    result = False

    while index < depths:

        if item['budget_code'] in results[index].keys():
            result = True
            break
        index += 1

    return result


def handle_ancestor_budgets(results, parent_budget_number, depths):

    if len(results) <= depths:
        results.append(dict())

    parent_data = None
    data_cursor = oracle.get_budget_by_budget_number(parent_budget_number)
    oracle_result = data_cursor.fetchall()
    data_cursor.close()
    if len(oracle_result) > 1:
        logger.error('More than one parent budget:')
        logger.error(oracle_result)
        logger.error('Child budget: %s' % parent_budget_number)

    parent = oracle_result[0]
    if parent[1].strip() != '':
        [results, parent_data] = handle_ancestor_budgets(results=results,
                                                         parent_budget_number=parent[1],
                                                         depths=depths+1)

    result = create_koha_data(parent, parent_data)

    if not exists_already_in_results(results, result, depths):
        results[depths][result['budget_code']] = result

    return [results, result]


def parse_data(results, data):
    if len(results) == 0:
        results.append(dict())

    parent_data = None
    if data['z76'][1] is not None and data['z76'][1].strip() != '':
        [results, parent_data] = handle_ancestor_budgets(results=results,
                                                         parent_budget_number=data['z76'][1],
                                                         depths=1)

    result = create_koha_data(data['z76'], parent_data)
    if not exists_already_in_results(results, result, 0):
        results[0][data['z76'][0]] = result
    return results


def fetch_data(credentials):
    logger.info('Reading data from Oracle...')
    oracle.establish_connection(credentials)

    results = []

    data_cursor = oracle.get_budgets_for_open_orders()
    for query_result in data_cursor:
        split = split_budget_data(query_result)
        results = parse_data(results, split)

    data_cursor.close()
    oracle.close_connection()

    return results


def generate_insert_statements(data, columns):
    mapping_table_statement = import_table_statement = 'INSERT INTO aqbudgets ('
    keys_len = len(columns)

    for idx, key in enumerate(columns):

        if idx == keys_len - 1:
            import_table_statement += key

            mapping_table_statement += key
        else:
            import_table_statement += key + ','
            mapping_table_statement += key + ','

    import_table_statement += ')\nVALUES'
    mapping_table_statement += ')\nVALUES'

    counter = 0

    for aleph_key in data:
        budget = data[aleph_key]
        if counter != 0:
            import_table_statement += ','
            mapping_table_statement += ','

        import_table_statement += '\n('
        mapping_table_statement += '\n('

        for idx, key in enumerate(columns):

            if key == 'budget_parent_id':
                if 'parent_budget_code' in budget:
                    mariadbquery = mariadb.get_budget_by_code(budget_code=budget['parent_budget_code'].strip())
                    parent_id = mariadbquery[0]
                    if idx == keys_len - 1:
                        import_table_statement += '"' + str(parent_id) + '"'
                        mapping_table_statement += '"' + str(parent_id) + '"'
                    else:
                        import_table_statement += '"' + str(parent_id) + '",'
                        mapping_table_statement += '"' + str(parent_id) + '",'
                else:
                    if idx == keys_len - 1:
                        import_table_statement += 'NULL'
                        mapping_table_statement += 'NULL'
                    else:
                        import_table_statement += 'NULL,'
                        mapping_table_statement += 'NULL,'
            else:
                if idx == keys_len - 1:
                    if key in budget and budget[key] is not None:
                        import_table_statement += '"' + str(budget[key]).strip() + '"'
                        mapping_table_statement += '"' + str(budget[key]).strip() + '"'
                    else:
                        import_table_statement += 'NULL'
                        mapping_table_statement += 'NULL'
                else:
                    if key in budget and budget[key] is not None:
                        import_table_statement += '"' + str(budget[key]).strip() + '",'
                        mapping_table_statement += '"' + str(budget[key]).strip() + '",'
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

    data.reverse()
    database_columns = [
        'budget_parent_id', 'budget_code', 'budget_name', 'budget_branchcode', 'budget_amount', 'budget_encumb',
        'budget_expend', 'budget_notes', 'budget_period_id', 'sort1_authcat', 'sort2_authcat', 'budget_owner_id',
        'budget_permission'
    ]

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mariadb.establish_connection()
        cursor = mariadb.get_cursor()
        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        for current_depths_data in data:
            cursor = mariadb.get_cursor()

            [import_table_statement, mapping_table_statement] = \
                generate_insert_statements(current_depths_data, database_columns)

            import_file.write(import_table_statement)
            mapping_file.write(mapping_table_statement)

            cursor.execute(mapping_table_statement)

            mariadb.commit()

        cursor.close()


def start(credentials):
    mariadb.establish_connection()
    results = fetch_data(credentials)
    write_results(results)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
