import sys
import logging
import os

import lib.database_connections.mariadb as mariadb
import lib.database_connections.oracle as oracle

import lib.mappings.library_keys as library_keys
import lib.mappings.method_of_acquisition as method_of_acquisition

import lib.oracle_helper.dates as dates_helper
import lib.oracle_helper.z68 as z68

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/038000_aqbasket_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqbasket_data_import.sql'


def evaluate_is_standing(aleph_order_type):
    aleph_order_type = aleph_order_type.strip()

    if aleph_order_type == 'O':
        return 1

    return 0


def process_z68_data(previous_results, query_result, basket_groups):
    result = dict()

    parsed_open_date = dates_helper.process_aleph_date(query_result[6])
    if parsed_open_date is not None:
        result['creationdate'] = parsed_open_date

    if query_result[12] is None or library_keys.map_aleph_key(query_result[12].strip()) is None:
        logger.warning('No branch information for order ' + query_result[0] + '. Skipping...')
        return previous_results

    result['deliveryplace'] = library_keys.map_aleph_key(query_result[12].strip())
    result['billingplace'] = library_keys.map_aleph_key(query_result[12].strip())
    result['branch'] = library_keys.map_aleph_key(query_result[12].strip())

    if query_result[14] is not None:
        result['basketname'] = method_of_acquisition.map_aleph_key(query_result[14].strip())
    else:
        result['basketname'] = 'Automatically generated'

    parsed_order_date = dates_helper.process_aleph_date(query_result[15])
    if parsed_order_date is not None:
        result['closedate'] = parsed_order_date
    else:
        result['closedate'] = None

    if query_result[51] is not None:
        result['booksellernote'] = query_result[51].replace('\"', '\'')

    result['is_standing'] = z68.evaluate_is_standing(query_result[1])

    result['basketgroupid'] = basket_groups[query_result[0]][0]
    result['booksellerid'] = basket_groups[query_result[0]][3]

    previous_results[query_result[0]] = result

    return previous_results


def fetch_data(credentials):
    logger.info('Connecting...')
    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    logger.info('Connected...')

    aqbasketgroups_query = mariadb.get_aqbasketgroups()
    basket_groups = dict()
    for query_result in aqbasketgroups_query:
        basket_groups[query_result[-1]] = query_result

    z68_result = dict()
    z68_data_cursor = oracle.get_open_z68()
    logger.info('Processing data from z68 table...')
    for query_result in z68_data_cursor:
        z68_result = process_z68_data(z68_result, query_result, basket_groups)

    z68_data_cursor.close()

    oracle.close_connection()

    return z68_result


def generate_insert_statements(data_list, table_name, table_column_names):
    mapping_table_statement = import_table_statement = 'INSERT INTO ' + table_name + ' ('
    keys_len = len(table_column_names)

    for idx, key in enumerate(table_column_names):

        if idx == keys_len - 1:
            import_table_statement += key

            mapping_table_statement += key
            mapping_table_statement += ',ALEPH_Z68_REC_KEY'
        else:
            import_table_statement += key + ','
            mapping_table_statement += key + ','

    import_table_statement += ')\nVALUES'
    mapping_table_statement += ')\nVALUES'

    counter = 0

    for aleph_key in data_list:
        basket = data_list[aleph_key]
        if counter != 0:
            import_table_statement += ','
            mapping_table_statement += ','

        import_table_statement += '\n('
        mapping_table_statement += '\n('

        for idx, key in enumerate(table_column_names):
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


def write_data(data):
    logger.info('Writing data to file and mapping database.')

    database_columns = [
        'basketname', 'note', 'booksellernote', 'contractnumber', 'creationdate', 'closedate', 'booksellerid',
        'authorisedby', 'booksellerinvoicenumber', 'basketgroupid', 'deliveryplace', 'billingplace', 'branch',
        'is_standing', 'create_items'
    ]

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        [import_table_statement, mapping_table_statement] = \
            generate_insert_statements(data, 'aqbasket', database_columns)

        import_file.write(import_table_statement)

        mapping_file.write(mapping_table_statement)
        cursor.execute(mapping_table_statement)

        mariadb.commit()
        cursor.close()


def start(credentials):
    results = fetch_data(credentials)
    write_data(results)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
