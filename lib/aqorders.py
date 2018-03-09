import logging
import sys
import os

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.dates as dates_helper
import lib.mappings.currency as currency
import lib.mappings.order_status as order_status_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MISSING_ITEM_DATA = []
MISSING_BASKET = []

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/050000_aqorders_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqorders_data_import.sql'


def get_biblio_number(key, z30_data):
    if key in z30_data:
        return z30_data[key][0][0:9]


def process_open_order(data):
    result = dict()

    result['currency'] = currency.map_from_currency(data[33], True)
    result['unitprice'] = currency.parse_value(data[31])
    result['unitprice_tax_included'] = currency.parse_value(data[31])
    result['listprice'] = currency.parse_value(data[34])
    result['ecost'] = currency.parse_value(data[37])
    result['ecost_tax_included'] = currency.parse_value(data[37])
    result['uncertainprice'] = 1

    return result


def process_z68_data(previous_results, z30_data, basket_data, data):

    aleph_rec_key = data[0]

    basket_no = None
    if aleph_rec_key in basket_data:
        basket_no = basket_data[aleph_rec_key][0]

    if basket_no is None:
        MISSING_BASKET.append(data)

    order_status = order_status_helper.map_aleph_key(data[7])

    internal_note = None
    if data[24] is not None:
        internal_note = data[24].replace('\"', '\'')

    suppliers_reference_nubmer = None
    if data[26] is not None:
        suppliers_reference_nubmer = data[26].replace('\"', '\'')

    vendor_note = None
    if data[27] is not None:
        vendor_note = data[27].replace('\"', '\'')

    quantity = int(data[30])  # TODO: Hack, remove once data has been corrected
    if quantity > 8:
        quantity = 8

    date_received = None
    quantity_received = 0
    if order_status == 'complete':
        date_received = dates_helper.process_aleph_date(data[8])
        quantity_received = quantity

    result = {
        'order_status': order_status,
        'datereceived': date_received,
        'order_internalnote': internal_note,
        'suppliers_reference_number': suppliers_reference_nubmer,
        'order_vendornote': vendor_note,
        'basketno': basket_no,
        'budget_id': 1,
        'biblionumber': get_biblio_number(data[2].strip(), z30_data),
        'quantity': quantity,
        'quantityreceived': quantity_received
    }

    if result['biblionumber'] is None:
        MISSING_ITEM_DATA.append(data)
        return previous_results

    if order_status_helper.is_open(data[7]):
        result = {**result, **process_open_order(data)}

    previous_results[aleph_rec_key] = result

    return previous_results

    # `entrydate` date DEFAULT NULL,
    # `quantity` smallint(6) DEFAULT NULL,
    # `listprice` decimal(28,6) DEFAULT NULL,
    # `invoiceid` int(11) DEFAULT NULL, # TODO
    # `freight` decimal(28,6) DEFAULT NULL,
    # `quantityreceived` smallint(6) NOT NULL DEFAULT 0,
    # `datecancellationprinted` date DEFAULT NULL,
    # `cancellationreason` text COLLATE utf8_unicode_ci DEFAULT NULL,
    # `purchaseordernumber` mediumtext COLLATE utf8_unicode_ci DEFAULT NULL,
    # `rrp` decimal(13,2) DEFAULT NULL,
    # `rrp_tax_excluded` decimal(28,6) DEFAULT NULL,
    # `rrp_tax_included` decimal(28,6) DEFAULT NULL,
    # `tax_rate_bak` decimal(6,4) DEFAULT NULL,
    # `tax_rate_on_ordering` decimal(6,4) DEFAULT NULL,
    # `tax_rate_on_receiving` decimal(6,4) DEFAULT NULL,
    # `tax_value_bak` decimal(28,6) DEFAULT NULL,
    # `tax_value_on_ordering` decimal(28,6) DEFAULT NULL,
    # `tax_value_on_receiving` decimal(28,6) DEFAULT NULL,
    # `discount` float(6,4) DEFAULT NULL,
    # `sort1` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `sort2` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `sort1_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `sort2_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `uncertainprice` tinyint(1) DEFAULT NULL,
    # `claims_count` int(11) DEFAULT 0,
    # `claimed_date` date DEFAULT NULL,
    # `subscriptionid` int(11) DEFAULT NULL, # TODO
    # `parent_ordernumber` int(11) DEFAULT NULL,
    # `line_item_id` varchar(35) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `suppliers_reference_number` varchar(35) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `suppliers_reference_qualifier` varchar(3) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `suppliers_report` text COLLATE utf8_unicode_ci DEFAULT NULL,
    # `ALEPH_Z68_DOC_NUMBER` varchar(25) NOT NULL,


def fetch_data(credentials):
    logger.info('Connecting...')
    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    logger.info('Connected.')

    logger.info('Fetching z30 data (items)...')
    z30_data = dict()
    z30_data_cursor = oracle.get_z30_with_order_number()
    for query_result in z30_data_cursor:
        z30_data[query_result[24].strip()] = query_result
    z30_data_cursor.close()
    logger.info('Done.')

    logger.info('Fetching basket data...')
    basket_data = dict()
    basket_data_cursor = mariadb.get_aqbaskets()
    for query_result in basket_data_cursor:
        basket_data[query_result[-1]] = query_result
    logger.info('Done.')

    results = dict()
    data_cursor = oracle.get_not_cancelled_z68()

    for query_result in data_cursor:
        results = process_z68_data(results, z30_data, basket_data, query_result)
    data_cursor.close()

    oracle.close_connection()

    return results


def generate_insert_statements(data_list, table_name, database_columns):
    mapping_table_statement = import_table_statement = 'INSERT INTO ' + table_name + ' ('
    keys_len = len(database_columns)

    for idx, key in enumerate(database_columns):

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

        for idx, key in enumerate(database_columns):
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
    database_columns = [
        'biblionumber', 'entrydate', 'quantity', 'currency', 'listprice', 'datereceived', 'invoiceid',
        'freight', 'unitprice', 'unitprice_tax_excluded', 'unitprice_tax_included', 'quantityreceived',
        'datecancellationprinted', 'cancellationreason', 'order_internalnote', 'order_vendornote',
        'purchaseordernumber', 'basketno', 'rrp', 'rrp_tax_excluded', 'rrp_tax_included', 'ecost', 'ecost_tax_excluded',
        'ecost_tax_included', 'tax_rate_bak', 'tax_rate_on_ordering', 'tax_rate_on_receiving', 'tax_value_bak',
        'tax_value_on_ordering', 'tax_value_on_receiving', 'discount', 'budget_id', 'budgetdate', 'sort1', 'sort2',
        'sort1_authcat', 'sort2_authcat', 'uncertainprice', 'claims_count', 'claimed_date', 'subscriptionid',
        'parent_ordernumber', 'orderstatus', 'line_item_id', 'suppliers_reference_number',
        'suppliers_reference_qualifier', 'suppliers_report'
    ]

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        [import_table_statement, mapping_table_statement] = \
            generate_insert_statements(data, 'aqorders', database_columns)

        import_file.write(import_table_statement)

        mapping_file.write(mapping_table_statement)
        cursor.execute(mapping_table_statement)

        mariadb.commit()
        cursor.close()


def start(oracle_credentials):
    results = fetch_data(oracle_credentials)

    logger.warning('%s Z68-orders have no matching Z30-items:', len(MISSING_ITEM_DATA))
    for missing in MISSING_ITEM_DATA:
        logger.warning(missing)

    logger.warning('%s Z68-orders have no matching basket:', len(MISSING_BASKET))
    for missing in MISSING_BASKET:
        logger.warning(missing)

    write_data(results)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
