import logging
import sys

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MAPPING_SQL_OUTPUT_PATH = './aleph_oracle_exports/mariadb_intermediate_values/00300_aqbasketgroups_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = './aleph_oracle_exports/ready_for_import/aqbasketgroups_data_import.sql'


def construct_name(query_result):
    return "[aleph order]" + query_result[0]


def process_68_data(existing_results, query_result):

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
    logger.info('Processing data from z70 table...')
    for query_result in z68_data_cursor:
        z68_result = process_68_data(z68_result, query_result)

    z68_data_cursor.close()

    oracle.close_connection()

    # Still unhandled fields for aqbookseller:
    # freedeliveryplace 	text 	65535 	 √  		null
    # deliverycomment 	varchar 	255 	 √  		null

    return z68_result


def generate_insert_statement(aleph_key, data, produce_mapping_table):
    statement = 'INSERT INTO aqbasketgroups ('

    keys = data.keys()
    keys_len = len(keys)
    for idx, key in enumerate(keys):
        if idx == keys_len - 1:
            statement += key

            if produce_mapping_table:
                statement += ', ALEPH_REC_KEY'
        else:
            statement += key + ','

    statement += ') VALUES('

    for idx, key in enumerate(keys):
        if idx == keys_len - 1:
            statement += '"' + str(data[key]) + '"'
            if produce_mapping_table:
                statement += ', "' + aleph_key + '"'
        else:
            statement += '"' + str(data[key]) + '",'

    statement += ')'
    statement += ';\n'

    return statement


def write_data(data):
    logger.info('Writing data to file and mapping database.')

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")

        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        for aleph_key in data.keys():

            import_file.write(generate_insert_statement(aleph_key, data[aleph_key], False))
            mapping_statement = generate_insert_statement(aleph_key, data[aleph_key], True)

            mapping_file.write(mapping_statement)
            cursor.execute(mapping_statement)

            mariadb.commit()

        cursor.close()


def start(credentials):
    results = fetch_data(credentials)

    write_data(results)


if __name__ == '__main__':

    import mappings.library_keys as library_keys
    import database_connections.mariadb as mariadb
    import database_connections.oracle as oracle

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
else:
    import aleph_oracle_exports.mappings.library_keys as library_keys
    import aleph_oracle_exports.database_connections.mariadb as mariadb
    import aleph_oracle_exports.database_connections.oracle as oracle
