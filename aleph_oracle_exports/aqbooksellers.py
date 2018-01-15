import logging
import sys

import re

import mappings.currency as currency
import database_connections.mariadb as mariadb
import database_connections.oracle as oracle
import oracle_helper.z70 as z70_helper
import oracle_helper.z72 as z72_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Global variables
TRIM_ADDRESS_REGEX = re.compile(r'\s{2,}', re.IGNORECASE)
MONOGRAPH = 'MONOGRAPH'
SERIAL = 'SERIAL'
MAPPING_SQL_OUTPUT_PATH = './aleph_oracle_exports/mariadb_intermediate_values/00100_aqbooksellers_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = './aleph_oracle_exports/ready_for_import/aqbooksellers_data_import.sql'


def escape_double_quotes(string):
    if string is None:
        return None
    else:
        return string.replace('\"', '\'')


# name kombiniert aus 'Name in Aleph'-'Aleph Lieferantentyp'-'(serials|monograph)'
def construct_name(query_result, postfix):
    if query_result[33] is None:
        return escape_double_quotes(query_result[7] + postfix)
    else:
        return escape_double_quotes(query_result[7] + '-' + query_result[33] + postfix)


# Aleph saves discount as '9(3)V99', meaning a string of 5 chars.
# first 3 represent the integer values, the last 2 are digits
def parse_discount(discount):
    if discount is None:
        return None

    return float(discount[0:-2] + "." + discount[-2:])


def create_z70_general(query_result):
    result = {
        'notes': escape_double_quotes(query_result[15]),
        'discount': parse_discount(query_result[17]),
        'currency': currency.map_from_currency(query_result[35], True),
        'invoiceprice': currency.map_from_currency(query_result[35], True),
        'listprice': currency.map_from_currency(query_result[35], True),
        # weitere Währungen (query_result 36-38) fehlen aktuell
    }

    return result


def create_z70_monograph(query_result):
    result = {
        'name': construct_name(query_result, '-monograph'),
        'deliverytime': query_result[23],
        'accountnumber': query_result[28],
    }

    return result


def create_z70_serial(query_result):
    result = {
        'name': construct_name(query_result, '-serials'),
        'deliverytime': query_result[26],
        'accountnumber': query_result[29],
    }

    return result


def process_z70_result(existing_results, query_result):

    key = z70_helper.split_rec_key(query_result[0])[0]

    general_result = create_z70_general(query_result)

    existing_results[key] = {
        MONOGRAPH: {
            **general_result, ** create_z70_monograph(query_result)
        },
        SERIAL: {
            **general_result, ** create_z70_serial(query_result)
        }
    }
    return existing_results


# Addresses in Aleph can contain a lot of whitespaces between relevant data, for example:
# Biblioteka Instytut Archeologi UG                                                                   Universytet Gdanski                                                                                 Frau mgr. Elzbieta Lademann                                                                         Ul. Bielanska 5
# This function is used to trim those whitespace, replacing each with ', '.
def trim_address(address):
    return escape_double_quotes(TRIM_ADDRESS_REGEX.sub(', ', address))


def create_z72(query_result, address_type):

    result = {
        ('address' + str(address_type)): trim_address(query_result[2]),
        'phone': query_result[3],
        'fax': query_result[4],
        'booksellerfax': query_result[4],
        'url': query_result[6],
        'booksellerurl': query_result[6],
        'postal': query_result[9]
    }

    return result


def process_z72_result(existing_results, query_result):

    split_rec_key = z72_helper.split_rec_key(query_result[0])
    aleph_vendor_code = split_rec_key[0]
    aleph_address_type = int(split_rec_key[1])

    # Ignore z72 results that are EDI contacts, because we don't use them currently and there is nowhere
    # to save the data in Koha anyway.
    if aleph_address_type == 5:
        return existing_results

    if aleph_address_type < 1 or aleph_address_type > 5:
        logger.error('Found unknown address type in z72: ' + str(aleph_address_type))
        logger.error('Vendor code: ' + aleph_vendor_code)
        return existing_results

    if aleph_vendor_code in existing_results:
        older_sibling = existing_results[aleph_vendor_code]

        if 'address' + str(aleph_address_type) in older_sibling:
            logger.error('address' + str(aleph_address_type) + ' is already set in ' + older_sibling)
            return existing_results

        # Ignore duplicate values in address-1, address-2, address-3 and address-4
        if query_result[2] in older_sibling.values():
            return existing_results

        older_sibling['address' + str(aleph_address_type)] = trim_address(query_result[2])
        existing_results[aleph_vendor_code] = older_sibling
    else:
        existing_results[aleph_vendor_code] = create_z72(query_result, aleph_address_type)

    return existing_results


def sanity_check_table_results(z70_result, z72_result):
    diff_z70_z72 = set(z70_result.keys()) - set(z72_result.keys())
    diff_z72_z70 = set(z72_result.keys()) - set(z70_result.keys())

    if len(diff_z70_z72) != 0:
        logger.error('Table z70 contains keys ' + str(diff_z70_z72) + ', but z72 does not. Removing data.')
        for key in diff_z70_z72:
            del z70_result[key]

    if len(diff_z72_z70) != 0:
        logger.error('Table z72 contains keys ' + str(diff_z72_z70) + ', but z70 does not. Removing data.')
        for key in diff_z72_z70:
            del z72_result[key]

    return [z70_result, z72_result]


def combine_table_results(z70_results, z72_results, hardcoded):
    result = dict()

    for key in z70_results.keys():
        result[key] = {
            MONOGRAPH: {
                **z70_results[key][MONOGRAPH], **z72_results[key], **hardcoded
            },
            SERIAL: {
                **z70_results[key][SERIAL], **z72_results[key], **hardcoded
            },
        }

    return result


def fetch_data(connection_credentials):
    logger.info('Connecting...')
    con = oracle.get_connection(connection_credentials)
    logger.info('Connected...')

    z70_result = dict()

    cur = con.cursor()
    cur.execute('SELECT * FROM Z70')
    for queryResult in cur:
        z70_result = process_z70_result(z70_result, queryResult)

    cur.execute('SELECT * FROM Z72')
    z72_result = dict()
    for queryResult in cur:
        z72_result = process_z72_result(z72_result, queryResult)

    [z70_result, z72_result] = sanity_check_table_results(z70_result, z72_result)

    hardcoded = {
        'active': 1,
    }

    combined_results = combine_table_results(z70_result, z72_result, hardcoded)

    # Still unhandled fields for aqbookseller:
    # 'othersupplier': '',
    # 'gstreg': '',
    # 'listincgst': '',
    # 'invoiceincgst': '',
    # 'tax_rate': '',

    cur.close()
    con.close()

    return combined_results


def generate_insert_statement(aleph_key, data, produce_mapping_table):
    statement = 'INSERT INTO aqbooksellers ('

    keys = data.keys()
    keys_len = len(keys)
    for idx, key in enumerate(keys):
        if idx == keys_len - 1:
            statement += key

            if produce_mapping_table:
                statement += ', ALEPH_VENDOR_KEY'
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

    db = mariadb.get_connection()

    cursor = db.cursor()
    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ';')

        for aleph_key in data.keys():

            import_file.write(generate_insert_statement(aleph_key, data[aleph_key][MONOGRAPH], False))
            import_file.write(generate_insert_statement(aleph_key, data[aleph_key][SERIAL], False))

            mapping_monograph = generate_insert_statement(aleph_key, data[aleph_key][MONOGRAPH], True)
            mapping_serial = generate_insert_statement(aleph_key, data[aleph_key][SERIAL], True)

            mapping_file.write(mapping_monograph)
            mapping_file.write(mapping_serial)

            cursor.execute(mapping_monograph)
            cursor.execute(mapping_serial)

    db.commit()


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    results = fetch_data(sys.argv[1])

    write_data(results)
