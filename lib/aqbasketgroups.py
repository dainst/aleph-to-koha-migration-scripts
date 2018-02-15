import logging
import sys
import os

import lib.mappings.library_keys as library_keys
import lib.database_connections.mariadb as mariadb
import lib.database_connections.oracle as oracle

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/00300_aqbasketgroups_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqbasketgroups_data_import.sql'


def construct_name(query_result):
    return "[aleph order]" + query_result[0]


def process_z68_data(existing_results, query_result):

    result = dict()

    vendor_key = query_result[25]

    if vendor_key is None:
        logger.warning('Vendor key in Z68 is None, Z68_REC_KEY:')
        logger.warning(' ' + query_result[0])
        logger.warning(' Skipping order.')
        return existing_results

    result['name'] = construct_name(query_result)
    result['closed'] = 0
    result['booksellerid'] = mariadb.get_aqbookseller_by_aleph_key(vendor_key)[0]
    result['deliveryplace'] = library_keys.map_aleph_key(query_result[12].strip())
    result['billingplace'] = library_keys.map_aleph_key(query_result[12].strip())

    existing_results[query_result[0]] = result

    return existing_results


def fetch_data(credentials):
    logger.info('Connecting...')
    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    logger.info('Connected...')

    z68_result = dict()
    z68_data_cursor = oracle.get_open_z68_monograph()
    logger.info('Processing data from z68 table...')
    for query_result in z68_data_cursor:
        z68_result = process_z68_data(z68_result, query_result)

    z68_data_cursor.close()

    oracle.close_connection()

    # Still unhandled fields for aqbookseller:
    # freedeliveryplace 	text 	65535 	 √  		null
    # deliverycomment 	varchar 	255 	 √  		null

    return z68_result

def get_insert_statements(data_list, table_name, table_column_names):
    mapping_table_statement = import_table_statement = 'INSERT INTO ' + table_name + ' ('
    keys_len = len(table_column_names)

    for idx, key in enumerate(table_column_names):

        if idx == keys_len - 1:
            import_table_statement += key

            mapping_table_statement += key
            mapping_table_statement += ', ALEPH_REC_KEY'
        else:
            import_table_statement += key + ','
            mapping_table_statement += key + ','

    import_table_statement += ')\nVALUES'
    mapping_table_statement += ')\nVALUES'

    counter = 0

    for aleph_key in data_list:
        basketgroup = data_list[aleph_key]
        if counter != 0:
            import_table_statement += ','
            mapping_table_statement += ','

        import_table_statement += '\n('
        mapping_table_statement += '\n('

        for idx, key in enumerate(table_column_names):
            if idx == keys_len - 1:

                if key in basketgroup and basketgroup[key] is not None:
                    import_table_statement += '"' + str(basketgroup[key]) + '"'
                    mapping_table_statement += '"' + str(basketgroup[key]) + '"'
                else:
                    import_table_statement += 'NULL'
                    mapping_table_statement += 'NULL'

                mapping_table_statement += ', "' + aleph_key + '"'
            else:

                if key in basketgroup and basketgroup[key] is not None:
                    import_table_statement += '"' + str(basketgroup[key]) + '",'
                    mapping_table_statement += '"' + str(basketgroup[key]) + '",'
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
        'name', 'closed', 'booksellerid', 'deliveryplace', 'freedeliveryplace', 'deliverycomment', 'billingplace'
    ]

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        [import_table_statement, mapping_table_statement] = \
            get_insert_statements(data, 'aqbasketgroups', database_columns)

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