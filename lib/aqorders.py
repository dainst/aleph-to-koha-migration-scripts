import logging
import sys
import os
import pickle

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.dates as dates_helper
import lib.mappings.currency as currency
import lib.mappings.order_status as order_status_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MISSING_BASKET = []

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/050000_aqorders_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqorders_data_import.sql'

MISSING_BUDGET = []
SYS_NUMBER_TO_BIB_ID_MAPPING = None
order_to_subscription_mapping = None
ORDER_COUNT = 0
NO_BIBLIOGRAPHIC_ID = []
BIBLIOGRAPHIC_ID_FOUND = []
MISSING_SUBSCRIPTION = []
FOUND_SUBSCRIPTION_COUNT = 0


def construct_probable_budget_code(data):
    order_type = data[2]

    # Check if a valid library code exists in z68 data
    if data[12] is not None and data[12].strip() != '':
        library_code = data[12].strip()
    else:
        logger.debug('No sub library information:')
        logger.debug(data)
        return None

    # Rewrite library code for Madrid without trailing D
    if library_code == 'MADRD':
        library_code = 'MADR'

    # Construct default pattern for most library budgets
    if order_type == 'S':
        budget_code = '%sSER-2018' % library_code
    elif order_type == 'O':
        budget_code = '%sFOR-2018' % library_code
    elif order_type == 'M':
        budget_code = '%sMON-2018' % library_code
    else:
        budget_code = '%s-2018' % library_code

    # Construct special pattern for Orient, and add Sanaa orders to Orient's budget
    if library_code == 'ORIEN' or library_code == 'SANAA':
        if order_type == 'O':
            budget_code = 'ORIENTF-2018'
        elif order_type == 'M':
            budget_code = 'ORIENTM-2018'
        else:
            budget_code = 'ORIENTG-2018'

    # Construct special pattern for Teheran
    if library_code == 'TEHER':
        budget_code = 'EURAS-TEHERAN-2018'

    # TODO: Mapping library key "KAIRO" as "ROM"

    return budget_code


def process_z68_data(previous_results, basket_data, koha_invoice, order_to_budget_data, order_to_title_id,  data):
    global MISSING_BUDGET
    global SYS_NUMBER_TO_BIB_ID_MAPPING
    global NO_BIBLIOGRAPHIC_ID
    global BIBLIOGRAPHIC_ID_FOUND
    global MISSING_SUBSCRIPTION
    global FOUND_SUBSCRIPTION_COUNT

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

    quantity = int(data[30])
    # TODO: Hack, remove once data has been corrected
    if quantity > 8:
        quantity = 8

    date_received = None
    quantity_received = 0
    if order_status == 'complete':
        date_received = dates_helper.process_aleph_date(data[10])
        quantity_received = quantity
        logger.debug('Complete order: %s' % data[2].strip())
        # TODO: How to evaluate from aleph data?

    if aleph_rec_key in order_to_budget_data:
        budget_code = order_to_budget_data[aleph_rec_key]
    else:
        budget_code = construct_probable_budget_code(data)

    aqinvoice_data = mariadb.get_budget_by_code(budget_code)

    if aqinvoice_data is not None:
        budget_id = aqinvoice_data[0]
    else:
        budget_id = None

    if budget_id is None:
        if data[2] is not None:
            order_number = data[2].strip()
        else:
            order_number = None
        MISSING_BUDGET.append(
            {
                'aleph_rec_key': aleph_rec_key,
                'order_number': order_number
            }
        )
        return previous_results

    try:
        sys_number = order_to_title_id[aleph_rec_key]
        koha_bib_id = SYS_NUMBER_TO_BIB_ID_MAPPING[sys_number]
        BIBLIOGRAPHIC_ID_FOUND.append(
            {
                'aleph_rec_key': aleph_rec_key,
                'order_number': data[2].strip(),
                'zenon_id': sys_number
            }
        )
    except KeyError:
        koha_bib_id = None
        NO_BIBLIOGRAPHIC_ID.append(
            {
                'aleph_rec_key': aleph_rec_key,
                'order_number': data[2].strip(),
                'order_type': data[1]
            }
        )

    result = {
        'order_status': order_status,
        'entrydate': dates_helper.process_aleph_date(data[6]),
        'datereceived': date_received,
        'order_internalnote': internal_note,
        'suppliers_reference_number': suppliers_reference_nubmer,
        'order_vendornote': vendor_note,
        'basketno': basket_no,
        'budget_id': budget_id,
        'biblionumber': koha_bib_id,
        'quantity': quantity,
        'quantityreceived': quantity_received,
        'currency': currency.map_from_currency(data[33], True),
        'unitprice': currency.parse_value(data[31]),
        'unitprice_tax_included': currency.parse_value(data[31]),
        'listprice': currency.parse_value(data[34]),
        'rrp': currency.parse_value(data[34]),
        'rrp_tax_excluded': currency.parse_value(data[34]),
        'rrp_tax_included': currency.parse_value(data[34]),
        'ecost': currency.parse_value(data[37]),
        'ecost_tax_excluded': currency.parse_value(data[37]),
        'ecost_tax_included': currency.parse_value(data[37]),
        'uncertainprice': 1,
        'invoiceid': koha_invoice,
        'discount': float(data[36][:-2] + '.' + data[36][-2:])
    }

    if data[1] == 'S':
        try:
            subscription = order_to_subscription_mapping[aleph_rec_key]
            result['subscriptionid'] = subscription['subscriptionid']
            FOUND_SUBSCRIPTION_COUNT += 1
        except KeyError as e:
            if aleph_rec_key not in MISSING_SUBSCRIPTION:
                logger.debug(f'No subscription associated with {aleph_rec_key} despite being a serial order (Aleph '
                             f'ORDER_TYPE = "S").')
                MISSING_SUBSCRIPTION += [{'aleph_rec_key': aleph_rec_key, 'biblionumber': koha_bib_id}]

    if aleph_rec_key in previous_results:
        previous_results[aleph_rec_key].append(result)
    else:
        previous_results[aleph_rec_key] = [result]

    return previous_results

    # `freight` decimal(28,6) DEFAULT NULL,
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
    # `sort1` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `sort2` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `sort1_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `sort2_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `claims_count` int(11) DEFAULT 0,
    # `claimed_date` date DEFAULT NULL,
    # `parent_ordernumber` int(11) DEFAULT NULL,
    # `line_item_id` varchar(35) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `suppliers_reference_number` varchar(35) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `suppliers_reference_qualifier` varchar(3) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `suppliers_report` text COLLATE utf8_unicode_ci DEFAULT NULL,
    # `ALEPH_Z68_DOC_NUMBER` varchar(25) NOT NULL,


def fetch_data(credentials):
    global ORDER_COUNT
    logger.info('Connecting...')
    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    logger.info('Connected.')

    logger.info('Fetching basket data...')
    basket_data = dict()
    basket_data_cursor = mariadb.get_aqbaskets()
    for query_result in basket_data_cursor:
        basket_data[query_result[-2]] = query_result
    logger.info('Done.')

    logger.info('Fetching budget data...')
    order_to_budget_mapping = dict()
    data_cursor = oracle.get_orders_to_budgets_mapping()
    for query_result in data_cursor:
        order_to_budget_mapping[query_result[0]] = query_result[1].strip()
    data_cursor.close()
    logger.info('Done.')

    logger.info('Fetching title IDs...')
    order_to_title_id = dict()
    data_cursor = oracle.get_order_to_zenon_id_pairs()
    for query_result in data_cursor:
        order_to_title_id[query_result[0]] = query_result[1]

    logger.info('Done.')

    logger.info('Processing z68 (orders) data...')
    results = dict()
    data_cursor = oracle.get_open_z68()
    for query_result in data_cursor:

        aqinvoice_data = mariadb.get_invoice_by_aleph_rec_key(query_result[0])
        if aqinvoice_data is not None:
            for koha_invoice in aqinvoice_data:
                # check if multiple z75/aqinvoices associated
                # for each, process data and set aqinvoices id
                ORDER_COUNT += 1
                results = process_z68_data(results, basket_data, koha_invoice[0], order_to_budget_mapping, order_to_title_id, query_result)
        else:
            results = process_z68_data(results, basket_data, None, order_to_budget_mapping, order_to_title_id, query_result)
    data_cursor.close()
    logger.info('Done.')

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
        order_list = data_list[aleph_key]
        for order in order_list:
            if counter != 0:
                import_table_statement += ','
                mapping_table_statement += ','

            import_table_statement += '\n('
            mapping_table_statement += '\n('

            for idx, key in enumerate(database_columns):
                if idx == keys_len - 1:

                    if key in order and order[key] is not None:
                        import_table_statement += '"' + str(order[key]) + '"'
                        mapping_table_statement += '"' + str(order[key]) + '"'
                    else:
                        import_table_statement += 'NULL'
                        mapping_table_statement += 'NULL'

                    mapping_table_statement += ', "' + aleph_key + '"'
                else:

                    if key in order and order[key] is not None:
                        import_table_statement += '"' + str(order[key]) + '",'
                        mapping_table_statement += '"' + str(order[key]) + '",'
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


def start(oracle_credentials, sys_number_to_bibliographic_number_mapping):
    global SYS_NUMBER_TO_BIB_ID_MAPPING
    global order_to_subscription_mapping

    SYS_NUMBER_TO_BIB_ID_MAPPING = sys_number_to_bibliographic_number_mapping

    with open(script_dir + '/../pickles/order_to_subscription_mapping.pickle', 'rb') as mapping_file:
        order_to_subscription_mapping = pickle.load(mapping_file)

    results = fetch_data(oracle_credentials)
    write_data(results)

    logger.info(f'{len(MISSING_SUBSCRIPTION)} serial orders of {FOUND_SUBSCRIPTION_COUNT + len(MISSING_SUBSCRIPTION)} missing subscription:')
    for item in MISSING_SUBSCRIPTION:
        logger.info(item)

    with open(script_dir + '/../log/missing_bibliographic_id.tsv', 'w') as error_log:
        logger.info('%i orders of %i without an associated bibliographic ID.' % (len(NO_BIBLIOGRAPHIC_ID), ORDER_COUNT))
        for item in NO_BIBLIOGRAPHIC_ID:
            logger.info('%s\t%s\n' % (item['aleph_rec_key'], item['order_number']))
            error_log.write('%s\t%s\n' % (item['aleph_rec_key'], item['order_number']))

    with open(script_dir + '/../log/successful_mapping.tsv', 'w') as log:
        for item in BIBLIOGRAPHIC_ID_FOUND:
            log.write('%s\t%s\t%s\n' % (item['aleph_rec_key'], item['order_number'], item['zenon_id']))


if __name__ == '__main__':

    if len(sys.argv) != 3:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.info('2) Path to mapping Zenon ID -> Koha bibliographic ID.')
        sys.exit()

    with open(sys.argv[2], 'rb') as output_file:
        sys_number_mapping = pickle.load(output_file)

    start(sys.argv[1], sys_number_mapping)
