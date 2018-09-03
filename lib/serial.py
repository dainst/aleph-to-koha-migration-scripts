import logging
import sys
import os
import pickle

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def generate_insert_statements(data_list, table, database_columns):
    import_table_statement = f'INSERT INTO {table} ('
    keys_len = len(database_columns)

    for idx, key in enumerate(database_columns):

        if idx == keys_len - 1:
            import_table_statement += key
        else:
            import_table_statement += key + ','

    import_table_statement += ')\nVALUES'

    counter = 0

    for values in data_list:
        if counter != 0:
            import_table_statement += ','

        import_table_statement += '\n('

        for idx, key in enumerate(database_columns):
            if idx == keys_len - 1:
                if key in values and values[key] is not None:
                    import_table_statement += '"' + str(values[key]) + '"'
                else:
                    import_table_statement += 'NULL'
            else:
                if key in values and values[key] is not None:
                    import_table_statement += '"' + str(values[key]) + '",'
                else:
                    import_table_statement += 'NULL,'

        import_table_statement += ')'
        counter = counter + 1

    import_table_statement += ';\n'

    return import_table_statement


def write_data(result_list, table, columns, import_sql_output_path, mapping_sql_output_path):

    with open(import_sql_output_path, 'w') as import_file, open(mapping_sql_output_path, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        import_table_statement = \
            generate_insert_statements(result_list, table, columns)

        import_file.write(import_table_statement)
        mapping_file.write(import_table_statement)
        cursor.execute(import_table_statement)

        mariadb.commit()
        cursor.close()


def start(credentials):
    logger.info('Connecting...')
    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    logger.info('Connected.')

    cursor = mariadb.get_item_barcode_and_itemnumber_pairs()
    barcode_to_item_number_mapping = dict()
    for barcode, itemnumber in cursor:
        barcode_to_item_number_mapping[barcode] = itemnumber

    subscription_to_item_mapping = dict()

    failed = []
    with open('pickles/order_to_subscription_mapping.pickle', 'rb') as file:
        contents = pickle.load(file)
        for key in contents:
            barcode_cursor = oracle.get_barcodes_by_z68_rec_key(key)

            for barcode, call_number in barcode_cursor:
                try:
                    if contents[key]['subscriptionid'] in subscription_to_item_mapping:
                        subscription_to_item_mapping[contents[key]['subscriptionid']] += [barcode_to_item_number_mapping[barcode.strip()]]
                    else:
                        subscription_to_item_mapping[contents[key]['subscriptionid']] = [barcode_to_item_number_mapping[barcode.strip()]]
                except KeyError:
                    failed += [barcode.strip()]

    logger.warning(f'Failed to map {len(failed)} barcodes to items: ')
    logger.warning(failed)

    logger.info('Fetching title IDs...')
    data_cursor = mariadb.get_subscription_id_and_biblionumber_pairs()
    serial_results = []
    serial_item_results = []
    counter = 1

    failed = []

    for biblionumber, subscriptionid in data_cursor:
        serial_results.append({
            'serialid': counter,
            'biblionumber': biblionumber,
            'subscriptionid': subscriptionid
        })
        try:
            for itemnumber in subscription_to_item_mapping[subscriptionid]:
                serial_item_results.append({
                    'itemnumber': itemnumber,
                    'serialid': counter
                })
        except KeyError as e:
            failed += [{'serialid': counter, 'biblionumber': biblionumber, 'subscriptionid': subscriptionid}]

        counter += 1

    logger.warning(f'Failed to map {len(failed)} subscriptions to items: ')
    logger.warning(failed)

    #  TODO: Bei den Zeitschriften habe ich einen komischen Fehler, bei dem für ein Exemplar zwei Abos vorhanden sind, dem muss ich noch einmal auf den Grund gehen:
    #  https://kohadev.dainst.org:8443/cgi-bin/koha/catalogue/detail.pl?biblionumber=149933 habe ich zwei Abos mit dem Exemplar mit dem Barcode 219074-190 verknüpft.
    #  Beide Abos sind der Bibliothek Frankfurt zugeordnet, einmal ist das Anfangsdatum der 2012-08-30 und einmal 2015-08-28. Es kann gut sein dass es ein Fehler in meinem Script ist,

    serial_table_columns = serial_results[0].keys()
    serial_items_table_columns = serial_item_results[0].keys()

    script_dir = os.path.dirname(__file__)

    write_data(serial_results,
               'serial',
               serial_table_columns,
               script_dir + '/ready_for_import/serial_data_import.sql',
               script_dir + '/mariadb_intermediate_values/019000_serial_data_mapping.sql'
               )

    write_data(serial_item_results,
               'serialitems',
               serial_items_table_columns,
               script_dir + '/ready_for_import/serialitems_data_import.sql',
               script_dir + '/mariadb_intermediate_values/146000_serialitems_data_mapping.sql'
               )


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])