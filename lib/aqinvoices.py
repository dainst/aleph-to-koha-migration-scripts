import logging
import sys
import os

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.dates as dates_helper
import lib.mappings.currency as currency
import lib.mappings.fallback_budgets as fallback_budgets

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/046000_aqinvoices_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqinvoices_data_import.sql'

AQINVOICESDATA = dict()
INVOICE_TO_BUDGET_MAPPING = dict()
MISSING_BUDGET_ALEPH = []
MISSING_BUDGET_KOHA = []


def split_join(query_result):
    result = {
        "z68": query_result[0:56],
        "z75": query_result[56:70],
        "z77": query_result[70:]
    }
    return result


def process_data(data):
    global AQINVOICESDATA
    global INVOICE_TO_BUDGET_MAPPING
    global MISSING_BUDGET_ALEPH
    global MISSING_BUDGET_KOHA

    if (data['z75'][0], data['z75'][1]) not in INVOICE_TO_BUDGET_MAPPING:
        MISSING_BUDGET_ALEPH.append((data['z75'][0], data['z75'][1]))
        koha_budget_id = mariadb.get_budget_by_code(
            fallback_budgets.get_budget_for_method_of_acquisition(data['z68'][14].strip())
        )[0]
    else:
        budget_code = INVOICE_TO_BUDGET_MAPPING[(data['z75'][0], data['z75'][1])].strip()

        if mariadb.get_budget_by_code(budget_code) is None:
            koha_budget_id = None
            MISSING_BUDGET_KOHA.append((data['z75'][0], data['z75'][1]))
        else:
            koha_budget_id = mariadb.get_budget_by_code(budget_code)[0]

    bookseller = mariadb.get_aqbookseller_by_aleph_vendor_key(data['z68'][25].strip())

    invoice_number = str(data['z77'][0][20:]).strip()

    result = {
        'invoicenumber': invoice_number,
        'booksellerid': bookseller[0],
        'shipmentdate': dates_helper.process_aleph_date(data['z77'][15]),
        'billingdate': dates_helper.process_aleph_date(data['z77'][13]),
        'closedate': dates_helper.process_aleph_date(data['z77'][18]),
        'shipmentcost': currency.parse_value(data['z77'][8]),
        'shipmentcost_budgetid': koha_budget_id,
        'ALEPH_Z75_REC_KEY_2': data['z75'][1],
        'ALEPH_Z68_REC_KEY': data['z68'][0]
    }
    AQINVOICESDATA[invoice_number] = result


def fetch_data(credentials):
    global INVOICE_TO_BUDGET_MAPPING

    oracle.establish_connection(credentials)
    mariadb.establish_connection()

    data_cursor = oracle.get_budget_to_invoice_mapping()
    for query_result in data_cursor:
        if (query_result[2], query_result[1]) in INVOICE_TO_BUDGET_MAPPING \
                and query_result[0] != INVOICE_TO_BUDGET_MAPPING[(query_result[2], query_result[1])]:
            logger.error(f'{(query_result[2], query_result[1])} already in budget mapping.')
            logger.error(f'New value: {query_result[0].strip()}, ' +
                         f'old value: {INVOICE_TO_BUDGET_MAPPING[(query_result[2], query_result[1])].strip()}.')

        INVOICE_TO_BUDGET_MAPPING[(query_result[2], query_result[1])] = query_result[0]
    data_cursor.close()

    data_cursor = oracle.get_budget_to_invoice_mapping_variant()
    for query_result in data_cursor:
        if (query_result[2], query_result[1]) in INVOICE_TO_BUDGET_MAPPING:
            continue
        INVOICE_TO_BUDGET_MAPPING[(query_result[2], query_result[1])] = query_result[0]
    data_cursor.close()

    data_cursor = oracle.get_open_z68_with_invoices()
    counter = 0
    for query_result in data_cursor:
        split = split_join(query_result)
        process_data(split)
        counter += 1
    data_cursor.close()

    logger.info(f'{len(MISSING_BUDGET_ALEPH)} of {counter} orders are missing an aleph budget.')

    with open(script_dir + '/../log/invoices_missing_aleph_budgets.log', 'w') as log_file:
        for rec_key, rec_key_2 in MISSING_BUDGET_ALEPH:
            logger.info(f'{rec_key}, {rec_key_2}')
            log_file.write(f'{rec_key},{rec_key_2}\n')

    logger.info(f'{len(MISSING_BUDGET_KOHA)} of {counter} orders are missing a koha budget.')
    with open(script_dir + '/../log/invoices_missing_koha_budgets.log', 'w') as log_file:
        for rec_key, rec_key_2 in MISSING_BUDGET_KOHA:
            logger.info(f'{rec_key}, {rec_key_2}')
            log_file.write(f'{rec_key},{rec_key_2}\n')

    oracle.close_connection()


def generate_import_statements():
    global AQINVOICESDATA

    insert_statement = mapping_statement = 'INSERT INTO aqinvoices ('
    column_names = ['invoicenumber', 'booksellerid', 'shipmentdate', 'billingdate',
                    'closedate', 'shipmentcost', 'shipmentcost_budgetid']
    first_column = True
    for name in column_names:
        if not first_column:
            insert_statement += ','
            mapping_statement += ','
        first_column = False

        insert_statement += name
        mapping_statement += name

    insert_statement += ')\nVALUES'
    mapping_statement += ',ALEPH_Z75_REC_KEY_2,ALEPH_Z68_REC_KEY)\nVALUES'

    first_row = True
    for aleph_key in AQINVOICESDATA:
        period = AQINVOICESDATA[aleph_key]

        if not first_row:
            insert_statement += ','
            mapping_statement += ','
        first_row = False

        insert_statement += '\n('
        mapping_statement += '\n('

        first_column = True
        for name in column_names:
            if not first_column:
                insert_statement += ','
                mapping_statement += ','
            first_column = False
            if name in period and period[name] is not None:
                insert_statement += '"%s"' % str(period[name])
                mapping_statement += '"%s"' % str(period[name])
            else:
                insert_statement += 'NULL'
                mapping_statement += 'NULL'

        insert_statement += ')'
        mapping_statement += ',"%s", "%s")' % (period['ALEPH_Z75_REC_KEY_2'], period['ALEPH_Z68_REC_KEY'])

    return [insert_statement, mapping_statement]


def write_data():
    global IMPORT_SQL_OUTPUT_PATH
    global MAPPING_SQL_OUTPUT_PATH

    [insert_statement, mapping_statement] = generate_import_statements()

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")

        import_file.write(insert_statement)
        mapping_file.write(mapping_statement)

        mariadb.establish_connection()

        cursor = mariadb.get_cursor()
        cursor.execute(mapping_statement)
        mariadb.commit()
        cursor.close()


def start(credentials):
    logger.info('Fetching invoices data...')
    fetch_data(credentials)
    logger.info('Writing data.')
    write_data()
    logger.info('Done.')


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
