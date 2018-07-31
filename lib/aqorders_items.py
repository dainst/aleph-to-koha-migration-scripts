import sys
import os
import logging
import lib.database_connections.mariadb as mariadb
import lib.database_connections.oracle as oracledb

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/117000_aqorders_items_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqorders_items_data_import.sql'


def import_item_data(item_data_path):
    cursor = mariadb.get_cursor()
    for line in open(item_data_path):
        if line.strip():
            cursor.execute(line)


def process_data(credentials, item_data_path):
    logger.info('Processing data...')

    mariadb.establish_connection()
    oracledb.establish_connection(credentials)

    import_item_data(item_data_path)

    barcode_to_koha_order_mapping = dict()
    results = []

    logger.info('Creating mapping: barcode -> Koha order number.')
    koha_aleph_order_pairs = mariadb.get_koha_and_aleph_order_id_pairs()
    for pair in koha_aleph_order_pairs:
        koha_id, aleph_rec_key = pair

        barcode_query_cursor = oracledb.get_barcodes_by_z68_rec_key(aleph_rec_key)
        for query_result in barcode_query_cursor:
            barcode_to_koha_order_mapping[query_result[0].strip()] = koha_id

        barcode_query_cursor.close()

    logger.info('Creating Koha order number <-> item number pairs.')
    query_result = mariadb.get_item_barcode_and_itemnumber_pairs()
    for barcode, itemnumber in query_result:

        if barcode not in barcode_to_koha_order_mapping:
            # logger.warning(f'Could not map barcode {barcode} to any order, item {itemnumber}.')
            continue

        results.append({
            'ordernumber': barcode_to_koha_order_mapping[barcode],
            'itemnumber': itemnumber,
        })

    mariadb.close_mariadb_connection()
    oracledb.close_connection()

    return results


def write_results(results):
    logger.info('Writing results...')
    insert_statement = \
        'INSERT INTO `aqorders_items` (`ordernumber`, `itemnumber`) ' \
        'VALUES (' + str(results[0]['ordernumber']) + ', ' + str(results[0]['itemnumber']) + ')\n'

    counter = 1
    while counter < len(results):
        insert_statement += ',(' + str(results[counter]['ordernumber']) + ', ' + str(results[counter]['itemnumber']) + ')\n'
        counter += 1

    insert_statement += ';'

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        import_file.write(insert_statement)

        mapping_file.write(insert_statement)
        cursor.execute(insert_statement)

        mariadb.commit()
        cursor.close()

    logger.info('Done.')


def start(credentials, item_data_path):
    results = process_data(credentials, item_data_path)
    write_results(results)


if __name__ == '__main__':

    if len(sys.argv) != 3:
        logger.info('Please provide as arguments:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.info('2) File containing item SQL data exported from Koha.')
        sys.exit()

    start(sys.argv[1], sys.argv[2])
