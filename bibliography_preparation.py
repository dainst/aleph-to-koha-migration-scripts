from pymarc import MARCReader, MARCWriter

import logging
import os
import sys

import lib.database_connections.mariadb as mariadb
import lib.mappings.library_keys as library_keys
import lib.mappings.marc_mappings as marc_mappings
import lib.oracle_helper.dates as dates_helper

# This script currently serves the following purposes:
#   1) Mapping viable headings in the bibliographic data via String comparison (what Aleph also does internally)
#      to the authority data exported from Koha. In case of a match, Koha's internal authority ID gets
#      added to the bibliographic heading (subfield '9').
#   2) Library keys are mapped between Aleph and Koha. The keys got refactored in Koha, to add more naming consistency.

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler = logging.FileHandler('./bibliography_preparation.log')
# file_handler.setLevel(logging.INFO)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.ERROR)
# file_handler.setFormatter(formatter)
# console_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
# logger.addHandler(console_handler)

max_holdings = [None, 0]


def map_item_type(marc_field_952):
    koha_item_type = None

    if 'y' in marc_field_952:
        aleph_material_key = marc_field_952['y']
        koha_item_type = marc_mappings.map_material(aleph_material_key)

    return koha_item_type


def map_barcode(marc_field_952):
    koha_barcode = None

    if 'p' in marc_field_952:
        aleph_barcode = marc_field_952['p']
        if len(aleph_barcode) > 20:
            logger.error("Aleph 'barcode' length exceeds Koha 'barcode' length!")
        else:
            koha_barcode = aleph_barcode

    return koha_barcode


def map_call_number(marc_field_952):
    koha_call_number = None

    if 'o' in marc_field_952:
        aleph_call_number = marc_field_952['o']
        if len(aleph_call_number) > 255:
            logger.error("Aleph 'call number' length exceeds Koha 'call number' length!")
        else:
            koha_call_number = aleph_call_number

    return koha_call_number


def map_inventory_number(marc_field_952):
    koha_stock_number = None

    if 'i' in marc_field_952:
        aleph_inventory_number = marc_field_952['i']
        if len(aleph_inventory_number) > 32:
            logger.error("Aleph 'inventory number' length exceeds Koha 'stock number' length!")
        else:
            koha_stock_number = aleph_inventory_number

    return koha_stock_number


def rstrip_purchase_price(purchase_price):
    length = len(purchase_price)
    rindex = length - 1
    if length > 0:
        if not purchase_price[-1].isdigit():
            while rindex >= 0:
                if purchase_price[rindex].isdigit():
                    break
                rindex -= 1

            if rindex == 0:
                purchase_price = '0.00'
            else:
                purchase_price = purchase_price[0:rindex + 1]

    return purchase_price


def lstrip_purchase_price(purchase_price):
    lindex = 0
    if not purchase_price[0].isdigit():
        for char in purchase_price:
            if char.isdigit():
                break
            lindex += 1

        if lindex == len(purchase_price):
            purchase_price = '0.00'
        else:
            purchase_price = purchase_price[lindex:]

    return purchase_price


def map_purchase_price(marc_field_952):
    koha_purchase_price = None

    if 'g' in marc_field_952:
        aleph_purchase_price = marc_field_952['g']
        if aleph_purchase_price is not None:
            koha_purchase_price = aleph_purchase_price.strip().replace(',', '.')

            if not (koha_purchase_price[0].isdigit() and koha_purchase_price[-1].isdigit()):
                koha_purchase_price = lstrip_purchase_price(koha_purchase_price)
                koha_purchase_price = rstrip_purchase_price(koha_purchase_price)

                koha_purchase_price = '{0:.2f}'.format(float(koha_purchase_price))
                if len(koha_purchase_price) > 11:
                    logger.error('Koha purchase price length: %s', len(koha_purchase_price))
                    logger.error("Koha purchase price: %s", koha_purchase_price)

    return koha_purchase_price


def map_aleph_vendor_code(aleph_z70_vendor_code):
    for (aleph_code, koha_id) in ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING:
        # logger.info("aleph_code: %s", aleph_code)
        # logger.info("koha_id: %s", koha_id)
        if aleph_z70_vendor_code == aleph_code:
            return koha_id
    else:
        return ''


def map_source_of_acquisition(marc_field_952):
    source_of_acquisition = None

    if 'e' in marc_field_952:
        source_of_acquisition = marc_field_952['e']
        if source_of_acquisition is not None:
            # logger.info("Aleph vendor code: %s", source_of_acquisition)
            source_of_acquisition = map_aleph_vendor_code(source_of_acquisition)
            # logger.info("Koha bookseller name: %s", source_of_acquisition)

    return source_of_acquisition


def map_date_acquired(marc_field_952):
    date_acquired = None

    if 'd' in marc_field_952:
        date_acquired = dates_helper.process_aleph_date(marc_field_952['d'])

    return date_acquired


def map_shelving_location_code(marc_field_952):
    shelving_location_code = None

    if 'c' in marc_field_952:
        shelving_location_code = marc_mappings.map_shelving_location(marc_field_952['c'], marc_field_952['a'])

    return shelving_location_code


def map_holding_library(marc_field_952):
    holding_library_key = None

    if 'b' in marc_field_952:
        holding_library_key = library_keys.map_aleph_key(marc_field_952['b'])

    return holding_library_key


def map_owning_library(marc_field_952):
    owning_library_key = None

    if 'a' in marc_field_952:
        owning_library_key = library_keys.map_aleph_key(marc_field_952['a'])

    return owning_library_key


def check_required_subfields(marc_field_952):
    is_successful = False

    if all(subfields not in marc_field_952 for subfields in ('a', 'b')) or 'y' not in marc_field_952:
        logger.error(
            'Neither marc subfield 952$a and 952$b found nor subfield 952$y!')
    elif 'a' and 'b' not in marc_field_952:
        if 'a' not in marc_field_952:
            marc_field_952.add_subfield('a', marc_field_952['b'])
            logger.debug(
                'No marc subfield 952$a found! Copy subfield 952$b in subfield 952$a. Subfield 952$a = %s',
                marc_field_952['a']
            )
        if 'b' not in marc_field_952:
            marc_field_952.add_subfield('b', marc_field_952['a'])
            logger.debug(
                'No marc subfield 952$b found! Copy subfield 952$a in subfield 952$b. Subfield 952$b = %s',
                marc_field_952['b']
            )

        is_successful = True
    else:
        is_successful = True

    return is_successful


def prepare_holding_data(record):
    global max_holdings

    logger.info("Processing holding information of Marc record: %s ...", record.leader)

    is_record_format_error = False
    is_record_format_warning = False
    is_record_format_info = False
    is_record_format_debugging = False

    marc_holding_fields = record.get_fields('952')
    holding_field_no = len(marc_holding_fields)
    if holding_field_no > max_holdings[1]:
        max_holdings[0] = record.leader
        max_holdings[1] = holding_field_no

    logger.info("%s holding field(s) found.", holding_field_no)

    counter = 1
    for marc_field_952 in marc_holding_fields:
        logger.debug("Field No. %s: %s", counter, marc_field_952)

        # TODO Datentypen und Feldlängen zw. Aleph u. Koha abgleichen!
        if check_required_subfields(marc_field_952):

            # '952$a' Owning Library (required by Koha)
            koha_owning_library = map_owning_library(marc_field_952)
            if koha_owning_library is not None:
                marc_field_952['a'] = koha_owning_library
            else:
                logger.error(
                    'Field No. %s: No valid owning library key found: 952$a = "%s"', counter, marc_field_952['a'])
                logger.error('Field No. %s: Skipping field: %s', counter, marc_field_952)
                record.remove_field(marc_field_952)
                is_record_format_error = True
                counter += 1
                continue

            # '952$b' Holding library (required by Koha)
            koha_holding_library = map_holding_library(marc_field_952)
            if koha_holding_library is not None:
                marc_field_952['b'] = koha_holding_library
            else:
                logger.error(
                    'Field No. %s: No valid holding library key found: 952$b = "%s"', counter, marc_field_952['b'])
                logger.error('Field No. %s: Skipping field: %s', counter, marc_field_952)
                record.remove_field(marc_field_952)
                is_record_format_error = True
                counter += 1
                continue

            # '952$c' Shelving location code
            koha_shelving_location = map_shelving_location_code(marc_field_952)
            if koha_shelving_location is not None:
                marc_field_952['c'] = koha_shelving_location
                # logger.info('Field No. %s: shelving location found: 952$c = "%s"', counter, marc_field_952['c'])
            else:
                logger.info(
                    'Field No. %s: No valid shelving location found: 952$c = "%s"', counter, marc_field_952['c'])
                logger.debug('Field No. %s: Skipping subfield "c" in marc field %s', counter, marc_field_952)
                marc_field_952.delete_subfield('c')
                is_record_format_debugging = True

            # '952$d' Date acquired
            koha_date_acquired = map_date_acquired(marc_field_952)
            if koha_date_acquired is not None:
                marc_field_952['d'] = koha_date_acquired
            else:
                logger.info('Field No. %s: No valid "date aquired" found: 952$d = "%s"', counter, marc_field_952['d'])
                logger.debug('Field No. %s: Skipping subfield "d" in marc field %s', counter, marc_field_952)
                marc_field_952.delete_subfield('d')
                is_record_format_debugging = True

            # '952$e' Source of acquisition
            koha_source_of_acquisition = map_source_of_acquisition(marc_field_952)
            if koha_source_of_acquisition is not None:
                marc_field_952['e'] = koha_source_of_acquisition
            else:
                logger.info(
                    'Field No. %s: No valid "source of aquisition" found: 952$e = "%s"', counter, marc_field_952['e'])
                logger.debug('Field No. %s: Skipping subfield "e" in marc field %s', counter, marc_field_952)
                marc_field_952.delete_subfield('e')
                is_record_format_debugging = True

            # '952$f' Coded location qualifier
            # 'This has no function in Koha.'

            # '952$g' Purchase price
            koha_purchase_price = map_purchase_price(marc_field_952)
            if koha_purchase_price is not None:
                marc_field_952['g'] = koha_purchase_price
            else:
                logger.info('Field No. %s: No valid "purchase price" found: 952$g = "%s"', counter, marc_field_952['g'])
                logger.debug('Field No. %s: Skipping subfield "g" in marc field %s', counter, marc_field_952)
                marc_field_952.delete_subfield('g')
                is_record_format_debugging = True

            # TODO '952$h' Serial enumeration

            # '952$i' Inventory number
            #logger.info('Field No. %s: "inventory number" found: 952$o = "%s"', counter, marc_field_952['i'])
            koha_stock_number = map_inventory_number(marc_field_952)
            if koha_stock_number is not None:
                marc_field_952['i'] = koha_stock_number
            else:
                logger.info('Field No. %s: No valid "inventory number" found: 952$o = "%s"', counter, marc_field_952['i'])
                logger.debug('Field No. %s: Skipping subfield "i" in marc field %s', counter, marc_field_952)
                marc_field_952.delete_subfield('i')
                is_record_format_debugging = True

            # '952$j' Shelving control number -> currently not applicable for Aleph
            # '952$k' Unused in Koha.
            # '952$l' Total Checkouts -> currently not applicable for Aleph
            # '952$m' Total Renewals -> currently not applicable for Aleph
            # '952$n' Total Holds -> currently not applicable for Aleph

            # '952$o' Koha full call number
            koha_call_number = map_call_number(marc_field_952)
            if koha_call_number is not None:
                marc_field_952['o'] = koha_call_number
            else:
                logger.info('Field No. %s: No valid "call number" found: 952$o = "%s"', counter, marc_field_952['o'])
                logger.debug('Field No. %s: Skipping subfield "o" in marc field %s', counter, marc_field_952)
                marc_field_952.delete_subfield('o')
                is_record_format_debugging = True

            # '952$p' Barcode (required for circulation)
            koha_barcode = map_barcode(marc_field_952)
            if koha_barcode is not None:
                marc_field_952['p'] = koha_barcode
            else:
                logger.info('Field No. %s: No valid "barcode" found: 952$p = "%s"', counter, marc_field_952['p'])
                logger.debug('Field No. %s: Skipping subfield "p" in marc field %s', counter, marc_field_952)
                marc_field_952.delete_subfield('p')
                is_record_format_debugging = True

            # '952$q' Due date -> currently not applicable for Aleph
            # '952$r' Date last seen -> currently not applicable for Aleph
            # '952$s' Date last checked out -> currently not applicable for Aleph
            # '952$t' Copy number

            # '952$u' Uniform Resource Identifier

            # '952$v' Replacement price -> currently not applicable for Aleph
            # '952$w' Price effective from -> currently not applicable for Aleph

            # '952$x' Nonpublic note

            # '952$y' Item type (required by Koha)
            koha_item_type = map_item_type(marc_field_952)
            if koha_item_type is not None:
                marc_field_952['y'] = koha_item_type
            else:
                logger.error('Field No. %s: No valid item type found: 952$y = "%s"', counter, marc_field_952['y'])
                logger.error('Field No. %s: Skipping field: %s', counter, marc_field_952)
                record.remove_field(marc_field_952)
                is_record_format_error = True
                counter += 1
                continue

            # '952$z' Public note

            # '952$0' Withdrawn status
            # '952$1' Lost status
            # '952$2' Classification
            # '952$3' Materials specified
            # '952$4' Damaged status
            # '952$5' Use restrictions
            # '952$6' Koha normalized classification for sorting
            # '952$7' Not for loan
            # '952$8' Collection code
            # '952$9' Item number

        else:
            logger.error('Field No. %s: Skipping field: %s', counter, marc_field_952)
            record.remove_field(marc_field_952)
            is_record_format_error = True

        counter += 1

    if is_record_format_error:
        logger.error('In Record:\n%s', record)
    elif is_record_format_warning:
        logger.warning('In Record:\n%s', record)
    elif is_record_format_info:
        logger.info('In Record:\n%s', record)
    elif is_record_format_debugging:
        logger.debug('In Record:\n%s', record)

    logger.info("Marc Record '%s' process completed!\n", record.leader)

    return record


def link_bibliographic_headings_to_koha_authority_ids(bibliographic_record, heading_to_authority_id_mapping):
    for field in marc_mappings.AUTHORITY_FIELDS_TO_BIBLIOGRAPHIC_FIELDS_MAPPING:
        for bibliographic_record_field in bibliographic_record.get_fields(field[1]):
            koha_id = heading_to_authority_id_mapping.get(bibliographic_record_field.as_marc('utf8'))

            if koha_id is not None:
                bibliographic_record_field.add_subfield('9', koha_id)

    return bibliographic_record


def get_aleph_vendor_code_koha_bookseller_name_mapping():
    mariadb.open_mariadb_connection()
    result = mariadb.get_aleph_vendor_code_koha_aqbookseller_mapping()
    mariadb.close_mariadb_connection()

    return result


def process_bibliographic_data(input_path, output_path, mapping):
    with open(input_path, 'rb') as input_file:
        with open(output_path, 'wb') as output_file:
            reader = MARCReader(input_file, force_utf8=True)
            writer = MARCWriter(output_file)

            for record in reader:
                record = link_bibliographic_headings_to_koha_authority_ids(record, mapping)
                record = prepare_holding_data(record)
                # TODO: instead of deleting 999, move to different fields/subfields
                record.remove_fields('999')
                writer.write(record)

            reader.close()
            writer.close()


def create_authority_heading_to_authority_id_mapping(file_path):
    logger.info('Creating authority-heading-to-authority-id mapping based on exported authority data...')

    result = {}
    with open(file_path, 'rb') as authority_file:
        reader = MARCReader(authority_file, force_utf8=True)
        for authority_record in reader:
            for field in marc_mappings.AUTHORITY_FIELDS_TO_BIBLIOGRAPHIC_FIELDS_MAPPING:
                auth_field = field[0]
                if authority_record[auth_field] is not None:
                    heading = authority_record[auth_field].as_marc('utf-8')
                    result[heading] = authority_record['001'].data

    logger.info('Done.')

    return result


if __name__ == '__main__':
    if len(sys.argv) != 4:
        logger.info("Please provide as argument:")
        logger.info("1) Path to bibliograhic data (directory) exports from Aleph.")
        logger.info("2) Path to authority data (file) export from Koha.")
        logger.info("3) Path to output directory for results.")
        sys.exit()

    authority_heading_to_authority_id_mapping = create_authority_heading_to_authority_id_mapping(sys.argv[2])
    input_directory = sys.argv[1]
    output_directory = sys.argv[3]

    if not os.path.dirname(output_directory).endswith('/'):
        output_directory += '/'

    if not os.path.exists(os.path.dirname(output_directory)) and os.path.dirname(output_directory) != '':
        os.makedirs(os.path.dirname(output_directory))

    ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING = get_aleph_vendor_code_koha_bookseller_name_mapping()
    logger.debug("ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING:\n%s", ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING)

    for filename in os.listdir(input_directory):
        if filename.endswith('.mrc'):
            without_extension = os.path.splitext(filename)[0]
            logger.info("Processing file '%s' ...", filename)
            process_bibliographic_data(
                input_directory + '/' + filename,
                output_directory + without_extension + '-preprocessed.mrc',
                authority_heading_to_authority_id_mapping
            )
            logger.info("Process '%s' completed.\n", filename)

    logger.info("Holding field number maximum: %s (%s)", max_holdings[1], max_holdings[0])
