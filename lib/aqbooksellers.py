import logging
import sys

import re
import os

import lib.database_connections.mariadb as mariadb
import lib.database_connections.oracle as oracle
import lib.mappings.currency as currency
import lib.oracle_helper.z70 as z70_helper
import lib.oracle_helper.z72 as z72_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Both Aleph and Koha look similar when it comes to vendors (Aleph)/ booksellers (Koha). Both systems hold most data
# concerning vendor/bookseller data in two tables which have a 1:n relation. The first serves the core vendor/bookseller
# data ('aqbooksellers' in Koha and 'z70' in Aleph). The other lets you define multiple addresses (Aleph, table 'z72')
# or contacts (Koha, 'aqcontacts').
# There are several key differences:
# 1. Addresses in Koha are held in aqbooksellers, while Aleph has its own table. The z72 for a z70 dataset has to be
#   retrieved and mapped to 'aqbooksellers' address fields ('address1' to 'address4').
# 2. In Aleph, each vendor can have different delivery times and accountnumbers for either serials or monographs. This
#   concept does not exist in Koha, so we create two bookseller (monograph and serial) for each vendor in Aleph.
# For more information about Aleph tables see: confluence


TRIM_ADDRESS_REGEX = re.compile(r'\s{2,}', re.IGNORECASE)
script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/00100_aqbooksellers_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqbooksellers_data_import.sql'


def escape_double_quotes(string):
    if string is None:
        return None
    else:
        return string.replace('\"', '\'')


# A new name is combined from aus 'name in aleph'-'aleph vendortype'-'(serials|monograph)'
def construct_name(query_result, postfix):
    if query_result[33] is None:
        return escape_double_quotes(query_result[7] + postfix)
    else:
        return escape_double_quotes('[' + query_result[33] + ']' + query_result[7] + postfix)


# Aleph saves discount as '9(3)V99', meaning a string of 5 chars, where the first 3 represent the integer values and
# the last 2 are the digits.
def parse_discount(discount):
    if discount is None:
        return None

    return float(discount[0:-2] + "." + discount[-2:])


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

    }

    return result


def process_z70_result(existing_results, query_result):

    key = z70_helper.split_rec_key(query_result[0])[0]

    result = {
        'name': construct_name(query_result, ''),
        'notes': escape_double_quotes(query_result[15]),
        'discount': parse_discount(query_result[17]),
        'currency': currency.map_from_currency(query_result[35], True),
        'invoiceprice': currency.map_from_currency(query_result[35], True),
        'listprice': currency.map_from_currency(query_result[35], True),
        # weitere Währungen (query_result 36-38) fehlen aktuell
    }

    monograph_data_exists = True
    serials_data_exists = True

    # Check if delays for monographs and serials are equal and if there exists an account for monographs (28) or
    # serials (29).
    if query_result[23] == query_result[26] and query_result[28] is None:
        monograph_data_exists = False

    if query_result[23] == query_result[26] and query_result[29] is None:
        serials_data_exists = False
    # If specific data exists for both monographs and serial orders, create two separate Koha booksellers for monographs
    # and serials respectively.
    if monograph_data_exists and serials_data_exists:
        monograph_result = {
            'name': construct_name(query_result, '-monograph'),
            'deliverytime': query_result[23],
            'accountnumber': query_result[28],
        }

        serials_result = {
            'name': construct_name(query_result, '-serials'),
            'deliverytime': query_result[26],
            'accountnumber': query_result[29],
        }

        existing_results[key] = {
            'MONOGRAPH': {
                **result, ** monograph_result
            },
            'SERIAL': {
                **result, ** serials_result
            }
        }
    # Otherwise create only one bookseller. Put data in if
    elif monograph_data_exists:
        result['deliverytime'] = query_result[23]
        result['accountnumber'] = query_result[28]

        existing_results[key] = {
            'MONOGRAPH': result
        }
    elif serials_data_exists:
        result['deliverytime'] = query_result[26]
        result['accountnumber'] = query_result[29]

        existing_results[key] = {
            'SERIAL': result
        }
    else:
        existing_results[key] = {
            'UNSPECIFIED': result
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
        current_address = trim_address(query_result[2])
        if 'address' + str(aleph_address_type) in older_sibling:
            logger.error('address' + str(aleph_address_type) + ' is already set in ' + older_sibling)
            return existing_results

        # Ignore duplicate values in address-1, address-2, address-3 and address-4
        if query_result[2] in older_sibling.values():
            return existing_results

        exists_in_older = False

        # Check if an older sibling  (= previous z72 record for the same vendor) address is a substring of the current
        # address value or if the current address is a substring of the address in an older sibling. This
        # seems to be quite common for our data for some reason. In either case, the longer address is kept, the
        # 'substring' address skipped.
        for key in older_sibling.keys():
            if key.startswith('address'):
                if older_sibling[key] in current_address:
                    older_sibling[key] = current_address
                    exists_in_older = True
                if current_address in older_sibling[key]:
                    exists_in_older = True

        if not exists_in_older:
            older_sibling['address' + str(aleph_address_type)] = current_address

        existing_results[aleph_vendor_code] = older_sibling
    else:
        existing_results[aleph_vendor_code] = create_z72(query_result, aleph_address_type)

    return existing_results


def sanity_check_table_results(z70_result, z72_result):
    diff_z70_z72 = set(z70_result.keys()) - set(z72_result.keys())
    diff_z72_z70 = set(z72_result.keys()) - set(z70_result.keys())

    if len(diff_z70_z72) != 0:
        logger.warning('Table z70 contains keys ' + str(diff_z70_z72) + ', but z72 does not.')

    if len(diff_z72_z70) != 0:
        logger.warning('Table z72 contains keys ' + str(diff_z72_z70) + ', but z70 does not. Removing data.')
        for key in diff_z72_z70:
            del z72_result[key]

    return [z70_result, z72_result]


def combine_table_results(z70_results, z72_results, hardcoded):
    result = dict()

    for key in z70_results.keys():
        for type_key in z70_results[key]:
            temp = {
                **z70_results[key][type_key],
                **hardcoded
            }

            if key in z72_results:
                temp = {
                    **temp,
                    **z72_results[key]
                }

            if key not in result:
                result[key] = {}

            result[key][type_key] = temp

    return result


def fetch_data(connection_credentials):
    logger.info('Connecting...')
    oracle.establish_connection(connection_credentials)
    logger.info('Connected...')

    z70_result = dict()
    z70_data_cursor = oracle.get_z70()
    logger.info('Processing data from z70 table...')
    for query_result in z70_data_cursor:
        z70_result = process_z70_result(z70_result, query_result)
    z70_data_cursor.close()

    z72_result = dict()
    z72_data_cursor = oracle.get_z72()
    logger.info('Processing data from z72 table...')
    for query_result in z72_data_cursor:
        z72_result = process_z72_result(z72_result, query_result)
    z72_data_cursor.close()

    # Make sure there are no orphaned z72 rows (missing a vendor in z70)
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

    oracle.close_connection()

    return combined_results


def generate_insert_statements(data_list):
    database_columns = [
        'name', 'address1', 'address2', 'address3', 'address4', 'phone', 'accountnumber', 'othersupplier', 'currency',
        'booksellerfax', 'notes', 'bookselleremail', 'booksellerurl', 'postal', 'url', 'active', 'listprice',
        'invoiceprice', 'gstreg', 'listincgst', 'invoiceincgst', 'tax_rate', 'discount', 'fax', 'deliverytime'
    ]

    mapping_table_statement = import_table_statement = 'INSERT INTO aqbooksellers ('

    keys_len = len(database_columns)
    for idx, key in enumerate(database_columns):
        if idx == keys_len - 1:
            import_table_statement += key
            mapping_table_statement += key
            mapping_table_statement += ', ALEPH_VENDOR_KEY'
        else:
            import_table_statement += key + ','
            mapping_table_statement += key + ','

    import_table_statement += ')\nVALUES'
    mapping_table_statement += ')\nVALUES'

    counter = 0

    for aleph_key in data_list:
        data = data_list[aleph_key]

        for type_key in data:
            current_data = data[type_key]
            if counter != 0:
                import_table_statement += ','
                mapping_table_statement += ','

            import_table_statement += '\n('
            mapping_table_statement += '\n('
            for idx, key in enumerate(database_columns):
                if idx == keys_len - 1:

                    if key in current_data and current_data[key] is not None:
                        import_table_statement += '"' + str(current_data[key]) + '"'
                        mapping_table_statement += '"' + str(current_data[key]) + '"'
                    else:
                        import_table_statement += 'NULL'
                        mapping_table_statement += 'NULL'

                    mapping_table_statement += ', "' + aleph_key + '"'
                else:

                    if key in current_data and current_data[key] is not None:
                        import_table_statement += '"' + str(current_data[key]) + '",'
                        mapping_table_statement += '"' + str(current_data[key]) + '",'
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

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")

        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        sql_statements = generate_insert_statements(data)

        import_file.write(sql_statements[0])
        mapping_file.write(sql_statements[1])
        cursor.execute(sql_statements[1])

        mariadb.commit()

        cursor.close()


def start(oracle_credentials):
    results = fetch_data(oracle_credentials)
    write_data(results)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
