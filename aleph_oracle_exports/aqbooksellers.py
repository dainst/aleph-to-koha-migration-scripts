import logging
import sys

import cx_Oracle
import mappings.currency as currency
import re

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TRIM_ADDRESS_REGEX = re.compile(r"\s{2,}", re.IGNORECASE)


def split_aleph_z70_rec_key(aleph_z70_rec_key):
    return [aleph_z70_rec_key[0:-5].strip(), aleph_z70_rec_key[-5].strip()]


# name kombiniert aus 'Name in Aleph'-'Aleph Lieferantentyp'-'(serials|monograph)'
def construct_name(query_result, postfix):
    if query_result[33] is None:
        return query_result[7] + postfix
    else:
        return query_result[7] + '-' + query_result[33] + postfix


def create_z70_monograph(query_result):
    result = {
        'name': construct_name(query_result, '-monograph'),
        'notes': query_result[15],
        'discount': query_result[17],
        'deliverytime': query_result[23],
        'accountnumber': query_result[28],
        'currency': currency.map_from_currency(query_result[35]),
        'invoiceprice': currency.map_from_currency(query_result[35]),
        # weitere Währungen (query_result 36-38) fehlen aktuell
    }

    return result


def create_z70_serial(query_result):
    result = {
        'name': construct_name(query_result, '-serials'),
        'notes': query_result[15],
        'discount': query_result[17],
        'deliverytime': query_result[26],
        'accountnumber': query_result[29],
        'currency': currency.map_from_currency(query_result[35]),
        'invoiceprice': currency.map_from_currency(query_result[35]),
        # weitere Währungen (query_result 36-38) fehlen aktuell
    }

    return result


def process_z70_result(existing_results, query_result):

    key = split_aleph_z70_rec_key(query_result[0])[0]

    existing_results[key] = {
        'MONOGRAPH_BOOKSELLER': create_z70_monograph(query_result),
        'SERIAL_BOOOKSELLER': create_z70_serial(query_result),
    }
    return existing_results


# See:
def split_aleph_z72_rec_key(aleph_z72_rec_key):
    return [aleph_z72_rec_key[0:-1].strip(), aleph_z72_rec_key[-1].strip()]


def determine_address_type(aleph_z72_rec_key, output_index):
    split = split_aleph_z72_rec_key(aleph_z72_rec_key)

    if int(split[1]) == output_index:
        return split[0]
    else:
        return None


# Addresses in Aleph can contain a lot of whitespaces between relevant data, for example:
# Biblioteka Instytut Archeologi UG                                                                   Universytet Gdanski                                                                                 Frau mgr. Elzbieta Lademann                                                                         Ul. Bielanska 5
# This function is used to trim those whitespace, replacing each with ', '.
def trim_address(address):
    return TRIM_ADDRESS_REGEX.sub(', ', address)


def create_z72(query_result, address_type):

    result = {
        ('address' + str(address_type)): trim_address(query_result[2]),
        'phone': query_result[3],
        'fax': query_result[4],
        'booksellerfax': query_result[4],
        'url': query_result[6],
        'booksellerurl': query_result[6],
        'postal': query_result[9],
    }

    return result


def process_z72_result(existing_results, query_result):

    split_rec_key = split_aleph_z72_rec_key(query_result[0])
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
            logger.error('address' + str(aleph_address_type) + " is already set in " + older_sibling)
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
        logger.error('Table z70 contains keys ' + str(diff_z70_z72) + ", but z72 does not. Removing data.")
        for key in diff_z70_z72:
            del z70_result[key]

    if len(diff_z72_z70) != 0:
        logger.error('Table z72 contains keys ' + str(diff_z72_z70) + ", but z70 does not. Removing data.")
        for key in diff_z72_z70:
            del z72_result[key]

    return [z70_result, z72_result]


def combine_table_results(z70_results, z72_results, hardcoded):
    result = dict()

    for key in z70_results.keys():
        result[key] = {
            'MONOGRAPH_BOOKSELLER': {
                **z70_results[key]['MONOGRAPH_BOOKSELLER'], **z72_results[key], **hardcoded
            },
            'SERIAL_BOOOKSELLER': {
                **z70_results[key]['SERIAL_BOOOKSELLER'], **z72_results[key], **hardcoded
            },
        }

    return result


def get_connection(credentials):
    con = cx_Oracle.connect(credentials, encoding="UTF-8", nencoding="UTF-8")
    return con


def export_data(connection_credentials, output_path):
    logger.info('Connecting...')
    con = get_connection(connection_credentials)
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

    # for key in z70_result.keys():
    #    logger.info(key)
    #    logger.info(z70_result[key])
    # for key in z72_result:
    #    logger.info(key)
    #    logger.info(z72_result[key])

    hardcoded = {
        'active': 1,
    }

    combined_results = combine_table_results(z70_result, z72_result, hardcoded)

    for key in combined_results:
        logger.info(key)
        logger.info(combined_results[key])

    # Still unhandled fields for aqbookseller:
    # 'othersupplier': '',
    # 'listprice': '',
    # 'gstreg': '',
    # 'listincgst': '',
    # 'invoiceincgst': '',
    # 'tax_rate': '',

    cur.close()
    con.close()

    return combined_results


if __name__ == '__main__':

    if len(sys.argv) != 3:
        logger.info("Please provide as argument:")
        logger.info("1) Connection info and credentials, pattern: '%USER%/%PASSWORD%@%IP%/%SID%'.")
        logger.info("2) The output path.")
        sys.exit()

    result = export_data(sys.argv[1], sys.argv[2])
