import logging
import sys
import os

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.dates as dates_helper
import lib.mappings.currency as currency

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/046000_aqinvoices_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqinvoices_data_import.sql'

AQINVOICESDATA = dict()


def split_join(query_result):
    result = {
        "z601": query_result[:18],
        "z68": query_result[18:74],
        "z77": query_result[74:104],
        "z76": query_result[104:]
    }
    return result


def process_data(data):
    global AQINVOICESDATA
    invoice_number = str(data['z77'][0][20:]).strip()
    result = {
        'invoicenumber': invoice_number,
        'booksellerid': mariadb.get_aqbookseller_by_aleph_vendor_key(data['z77'][0][:20].strip())[0],
        'shipmentdate': dates_helper.process_aleph_date(data['z77'][15]),
        'billingdate': dates_helper.process_aleph_date(data['z77'][13]),
        'closedate': dates_helper.process_aleph_date(data['z77'][18]),
        'shipmentcost': currency.parse_value(data['z77'][8]),
        'shipmentcost_budgetid': mariadb.get_budget_by_code(data['z76'][0])[0],
        'ALEPH_Z68_REC_KEY': data['z68'][0]
    }

    AQINVOICESDATA[invoice_number] = result


def fetch_data(credentials):
    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    data_cursor = oracle.get_open_z68_with_invoices()

    for query_result in data_cursor:
        split = split_join(query_result)
        process_data(split)
    data_cursor.close()

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
    mapping_statement += ',ALEPH_Z68_REC_KEY)\nVALUES'

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
        mapping_statement += ',"%s")' % period['ALEPH_Z68_REC_KEY']

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
