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
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler = logging.FileHandler('./bibliography_preparation.log')
# file_handler.setLevel(logging.INFO)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.ERROR)
# file_handler.setFormatter(formatter)
# console_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
# logger.addHandler(console_handler)

holding_field_max = [None, 0]
holding_field_counter = 0
record_error_no = 0
file_error_no = 0
total_error_no = 0


def map_lost_status(subfield_9521):
    lost_status = '0'

    if subfield_9521 == 'MI' or subfield_9521 == 'MS' or subfield_9521 == 'Missing' or subfield_9521 == 'Misshelved':
        lost_status = '1'
    logger.debug("Field No. %s: 952$1 = '%s', valid 'lost status' found.", holding_field_counter, lost_status)

    return lost_status


def map_public_note(subfield_952z):
    if len(subfield_952z) < 1:
        logger.debug("Field No. %s: 952$z = '%s', no valid 'public note' found!",
                     holding_field_counter, subfield_952z)

        return None
    else:
        logger.debug("Field No. %s: 952$z = '%s', valid 'public note' found.",
                     holding_field_counter, subfield_952z)

        return subfield_952z


def map_item_type(subfield_952y):
    item_type = None

    if subfield_952y is None:
        logger.error("Field No. %s: No required subfield 'y' found!", holding_field_counter)
    else:
        item_type = marc_mappings.map_material(subfield_952y)

        if item_type is None:
            logger.error("Field No. %s: 952$y = '%s', no valid 'item type' code found!",
                         holding_field_counter, subfield_952y)
        else:
            logger.debug("Field No. %s: 952$y = '%s', valid 'item type' code found.",
                         holding_field_counter, item_type)

    return item_type


def map_nonpublic_note(subfield_952x):
    if len(subfield_952x) < 1:
        logger.debug("Field No. %s: 952$x = '%s', no valid 'nonpublic note' found!",
                     holding_field_counter, subfield_952x)

        return None
    else:
        logger.debug("Field No. %s: 952$x = '%s', valid 'nonpublic note' found.",
                     holding_field_counter, subfield_952x)

        return subfield_952x


def map_copy_number(subfield_952t):
    if 1 > len(subfield_952t) > 32:
        # logger.error("Aleph 'copy number' length exceeds Koha 'copy number' length!\n")
        logger.debug("Field No. %s: 952$t = '%s', no valid 'copy number' found!",
                     holding_field_counter, subfield_952t)

        return None
    else:
        logger.debug("Field No. %s: 952$t = '%s', valid 'copy number' found.",
                     holding_field_counter, subfield_952t)

        return subfield_952t


def map_barcode(subfield_952p):
    if 1 > len(subfield_952p) > 20:
        logger.error("Aleph 'barcode' length exceeds Koha 'barcode' length!\n")
        logger.warning("Field No. %s: 952$p = '%s', no valid 'barcode' found!",
                       holding_field_counter, subfield_952p)

        return None
    else:
        logger.debug("Field No. %s: 952$p = '%s', valid 'barcode' found.",
                     holding_field_counter, subfield_952p)

        return subfield_952p


def map_call_number(subfield_952o):
    if 1 > len(subfield_952o) > 255:
        # logger.error("Length of 'call number' not in between 1 and 255!\n")
        logger.debug("Field No. %s: 952$o = '%s', no valid 'call number' found!",
                     holding_field_counter, subfield_952o)

        return None
    else:
        logger.debug("Field No. %s: 952$o = '%s', valid 'call number' found.",
                     holding_field_counter, subfield_952o)

        return subfield_952o


def map_inventory_number(subfield_952i):
    if 1 > len(subfield_952i) > 32:
        # logger.error("Aleph 'inventory number' length exceeds Koha 'stock number' length!\n")
        logger.debug("Field No. %s: 952$i = '%s', no valid 'inventory number' found!",
                     holding_field_counter, subfield_952i)

        return None
    else:
        logger.debug("Field No. %s: 952$i = '%s', valid 'inventory number' found.",
                     holding_field_counter, subfield_952i)

        return subfield_952i


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


def format_purchase_price(aleph_purchase_price):
    purchase_price = aleph_purchase_price.strip().replace(',', '.')

    if not (purchase_price[0].isdigit() and purchase_price[-1].isdigit()):
        purchase_price = lstrip_purchase_price(purchase_price)
        purchase_price = rstrip_purchase_price(purchase_price)
        purchase_price = '{0:.2f}'.format(float(purchase_price))

    if 1 > len(purchase_price) > 11:
        # logger.error('Koha purchase price length: %s', len(koha_purchase_price))
        # logger.error("Koha purchase price: %s", koha_purchase_price)

        return None
    else:

        return purchase_price


def map_purchase_price(subfield_952g):
    purchase_price = format_purchase_price(subfield_952g)

    if purchase_price is None:
        pass
        logger.debug("Field No. %s: 952$g = '%s', no valid 'purchase price' found!",
                     holding_field_counter, subfield_952g)
    else:
        pass
        logger.debug("Field No. %s: 952$g = '%s', valid 'purchase price' found.",
                     holding_field_counter, purchase_price)

    return purchase_price


def map_aleph_vendor_code(aleph_z70_vendor_code):
    for (aleph_code, koha_id) in ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING:
        # logger.info("aleph_code: %s", aleph_code)
        # logger.info("koha_id: %s", koha_id)
        if aleph_z70_vendor_code == aleph_code:

            return koha_id
    else:

        return None


def map_source_of_acquisition(subfield_952e):
    source_of_acquisition = map_aleph_vendor_code(subfield_952e)

    if source_of_acquisition is None:
        pass
        logger.debug("Field No. %s: 952$e = '%s', no valid 'source of aquisition' found!",
                     holding_field_counter, subfield_952e)
    else:
        pass
        logger.debug("Field No. %s: 952$e = '%s', valid 'source of aquisition' found.",
                     holding_field_counter, source_of_acquisition)

    return source_of_acquisition


def map_date_acquired(subfield_952d):
    date_acquired = dates_helper.process_aleph_date(subfield_952d)

    if date_acquired is None:
        logger.debug("Field No. %s: 952$d = '%s', no valid 'date aquired' found!",
                     holding_field_counter, subfield_952d)
    else:
        logger.debug("Field No. %s: 952$d = '%s', valid 'date aquired' found.",
                     holding_field_counter, date_acquired)

    return date_acquired


def map_shelving_location_code(subfield_952c, koha_library_code):
    shelving_location_code = marc_mappings.map_shelving_location(subfield_952c, koha_library_code)

    if shelving_location_code is None:
        logger.debug("Field No. %s: 952$c = '%s', no 'valid shelving location' found!",
                     holding_field_counter, subfield_952c)
    else:
        logger.debug("Field No. %s: 952$c = '%s', valid 'shelving location' found.",
                     holding_field_counter, shelving_location_code)

    return shelving_location_code


def map_holding_library(subfield_952b):
    holding_library = None

    if subfield_952b is None:
        logger.error("Field No. %s: No required subfield 'b' found!", holding_field_counter)
    else:
        holding_library = library_keys.map_aleph_key(subfield_952b)
        if holding_library is None:
            logger.error("Field No. %s: 952$b = '%s', no valid 'holding library' code found!",
                         holding_field_counter, subfield_952b)
        else:
            logger.debug("Field No. %s: 952$b = '%s', valid 'holding library' code found.",
                         holding_field_counter, holding_library)

    return holding_library


def map_owning_library(subfield_952a):
    owning_library = None

    if subfield_952a is None:
        logger.error("Field No. %s: No required subfield 'a' found!", holding_field_counter)
    else:
        owning_library = library_keys.map_aleph_key(subfield_952a)
        if owning_library is None:
            logger.error("Field No. %s: 952$a = '%s' , no valid 'owning library' code found!",
                         holding_field_counter, subfield_952a)
        else:
            logger.debug("Field No. %s: 952$a = '%s', valid 'owning library' code found.",
                         holding_field_counter, owning_library)

    return owning_library


def check_required_subfields(marc_field_952):
    is_success = False

    if all(subfields in marc_field_952 for subfields in ('a', 'b', 'y')):
        logger.debug("Field No. %s: All required subfieds 'a', 'b', and 'y' found.", holding_field_counter)
        is_success = True
    elif 'y' in marc_field_952 and ('a' or 'b' in marc_field_952):
        if 'a' not in marc_field_952:
            marc_field_952.add_subfield('a', marc_field_952['b'])
            logger.debug(
                "Field No. %s: Required subfield 'a' not found! Copy subfield 'b' into subfield 'a': 952$a = %s",
                holding_field_counter, marc_field_952['a']
            )
        if 'b' not in marc_field_952:
            marc_field_952.add_subfield('b', marc_field_952['a'])
            logger.debug(
                "Field No. %s: Required subfield 'b' not found! Copy subfield 'a' into subfield 'b': 952$b = %s",
                holding_field_counter, marc_field_952['b']
            )
        is_success = True
    else:
        logger.error('Field No. %s: Neither required subfields 952$a and 952$b found nor required subfield 952$y!',
                     holding_field_counter)

    return is_success


def prepare_holding_data(record):
    global holding_field_max
    global holding_field_counter
    global file_error_no
    global record_error_no

    logger.info("Processing holding information of Marc record: '%s' ...", record.leader)

    is_record_format_error = False
    is_record_format_warning = False
    is_record_format_info = False
    is_record_format_debugging = False

    marc_holding_fields = record.get_fields('952')
    holding_field_no = len(marc_holding_fields)
    if holding_field_no > holding_field_max[1]:
        holding_field_max[0] = record.leader
        holding_field_max[1] = holding_field_no

    logger.info("%s holding field(s) found.", holding_field_no)

    holding_field_counter = 1
    record_error_no = 0
    for marc_field_952 in marc_holding_fields:
        logger.debug("Field No. %s: %s", holding_field_counter, marc_field_952)

        if check_required_subfields(marc_field_952):

            # '952$a' Owning Library (required by Koha)
            koha_owning_library = map_owning_library(marc_field_952['a'])
            if koha_owning_library is None:
                logger.error('Field No. %s: Skipping field: %s', holding_field_counter, marc_field_952)
                record.remove_field(marc_field_952)
                is_record_format_error = True
                record_error_no += 1
                holding_field_counter += 1
                continue
            else:
                marc_field_952['a'] = koha_owning_library

            # '952$b' Holding library (required by Koha)
            koha_holding_library = map_holding_library(marc_field_952['b'])
            if koha_holding_library is None:
                logger.error('Field No. %s: Skipping field: %s', holding_field_counter, marc_field_952)
                record.remove_field(marc_field_952)
                is_record_format_error = True
                record_error_no += 1
                holding_field_counter += 1
                continue
            else:
                marc_field_952['b'] = koha_holding_library

            # '952$c' Shelving location code
            subfield_952c = marc_field_952['c']
            if subfield_952c is not None:
                koha_shelving_location = map_shelving_location_code(subfield_952c, koha_owning_library)
                if koha_shelving_location is None:
                    logger.info("Field No. %s: Skipping subfield 'c' in marc field %s",
                                holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('c')
                else:
                    marc_field_952['c'] = koha_shelving_location

            # '952$d' Date acquired
            subfield_952d = marc_field_952['d']
            if subfield_952d is not None:
                koha_date_acquired = map_date_acquired(subfield_952d)
                if koha_date_acquired is None:
                    logger.info("Field No. %s: Skipping subfield 'd' in marc field %s",
                                holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('d')
                else:
                    marc_field_952['d'] = koha_date_acquired

            # '952$e' Source of acquisition
            subfield_952e = marc_field_952['e']
            if subfield_952e is not None:
                koha_source_of_aquisition = map_source_of_acquisition(subfield_952e)
                if koha_source_of_aquisition is None:
                    logger.info("Field No. %s: Skipping subfield 'e' in marc field %s",
                                holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('e')
                else:
                    marc_field_952['e'] = koha_source_of_aquisition

            # '952$f' Coded location qualifier
            # 'This has no function in Koha.'

            # '952$g' Purchase price
            subfield_952g = marc_field_952['g']
            if subfield_952g is not None:
                koha_purchase_prise = map_purchase_price(subfield_952g)
                if koha_purchase_prise is None:
                    logger.info("Field No. %s: Skipping subfield 'g' in marc field %s",
                                holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('g')
                else:
                    marc_field_952['g'] = koha_purchase_prise

            # TODO '952$h' Serial enumeration
            subfield_952h = marc_field_952['h']
            if subfield_952h is not None:
                pass

            # '952$i' Inventory number
            subfield_952i = marc_field_952['i']
            if subfield_952i is not None:
                koha_inventory_number = map_inventory_number(subfield_952i)
                if koha_inventory_number is None:
                    logger.info("Field No. %s: Skipping subfield 'i' in marc field %s",
                                holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('i')
                else:
                    marc_field_952['i'] = koha_inventory_number

            # '952$j' Shelving control number -> currently not applicable for Aleph
            # '952$k' Unused in Koha.
            # '952$l' Total Checkouts -> currently not applicable for Aleph
            # '952$m' Total Renewals -> currently not applicable for Aleph
            # '952$n' Total Holds -> currently not applicable for Aleph

            # '952$o' Koha full call number
            subfield_952o = marc_field_952['o']
            if subfield_952o is not None:
                koha_call_number = map_call_number(subfield_952o)
                if koha_call_number is None:
                    logger.info("Field No. %s: Skipping subfield 'o' in marc field %s",
                                holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('o')
                else:
                    marc_field_952['o'] = koha_call_number

            # '952$p' Barcode (required for circulation)
            subfield_952p = marc_field_952['p']
            if subfield_952p is None:
                logger.warning("Field No. %s: No required subfield 'p' found!", holding_field_counter)
            else:
                koha_barcode = map_barcode(subfield_952p)
                if koha_barcode is None:
                    logger.warning("Field No. %s: Skipping subfield 'p' in marc field %s",
                                   holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('p')
                    is_record_format_error = True
                    record_error_no += 1
                else:
                    marc_field_952['p'] = koha_barcode

            # '952$q' Due date -> currently not applicable for Aleph
            # '952$r' Date last seen -> currently not applicable for Aleph
            # '952$s' Date last checked out -> currently not applicable for Aleph

            # '952$t' Copy number
            subfield_952t = marc_field_952['t']
            if subfield_952t is not None:
                koha_copy_number = map_copy_number(subfield_952t)
                if koha_copy_number is None:
                    logger.info("Field No. %s: Skipping subfield 't' in marc field %s",
                                holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('t')
                else:
                    marc_field_952['t'] = koha_copy_number

            # '952$u' Uniform Resource Identifier -> currently not applicable for Aleph
            # '952$v' Replacement price -> currently not applicable for Aleph
            # '952$w' Price effective from -> currently not applicable for Aleph

            # '952$x' Nonpublic note
            subfield_952x = marc_field_952['x']
            if subfield_952x is not None:
                koha_nonpublic_note = map_nonpublic_note(subfield_952x)
                if koha_nonpublic_note is None:
                    logger.info("Field No. %s: Skipping subfield 'x' in marc field %s",
                                holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('x')
                else:
                    marc_field_952['x'] = koha_nonpublic_note

            # '952$y' Item type (required by Koha)
            koha_item_type = map_item_type(marc_field_952['y'])
            if koha_item_type is None:
                logger.error('Field No. %s: Skipping field: %s', holding_field_counter, marc_field_952)
                record.remove_field(marc_field_952)
                is_record_format_error = True
                record_error_no += 1
                holding_field_counter += 1
                continue
            else:
                marc_field_952['y'] = koha_item_type

            # '952$z' Public note
            subfield_952z = marc_field_952['z']
            if subfield_952z is not None:
                koha_public_note = map_public_note(subfield_952z)
                if koha_public_note is None:
                    logger.info("Field No. %s: Skipping subfield 'z' in marc field %s",
                                holding_field_counter, marc_field_952)
                    marc_field_952.delete_subfield('z')
                else:
                    marc_field_952['z'] = koha_public_note

            # '952$0' Withdrawn status -> not applicable for Aleph

            # '952$1' Lost status
            subfield_9521 = marc_field_952['1']
            if subfield_9521 is not None:
                marc_field_952['1'] = map_lost_status(subfield_9521)

            # '952$2' Classification

            # '952$3' Materials specified -> not applicable for Aleph

            # '952$4' Damaged status

            # '952$5' Use restrictions

            # '952$6' Koha normalized classification for sorting -> not applicable for Aleph

            # '952$7' Not for loan

            # '952$8' Collection code -> not applicable for Aleph
            # '952$9' Item number (autogenerated) -> not applicable for Aleph

            # '952$A' Bestellnummer aus der Erwerbung

            # '952$C' Umlauf-Notiz
            # '952$D' Beschreibung
            # '952$E' Erwartet zum(Zeitschriftenheft)
            # '952$H' Jahreszählung bei Zetischriftenheften
            # '952$J' Ex.status
            # '952$O' 2.Signatur
            # '952$P' Erfassungsdatum
            # '952$S' Ex-Geschäftsgang-Status
            # '952$T' Statistikwerte
            # '952$U' Änderungsdatum

        else:
            logger.error('Field No. %s: Skipping field: %s', holding_field_counter, marc_field_952)
            record.remove_field(marc_field_952)
            is_record_format_error = True
            record_error_no += 1

        holding_field_counter += 1

    if is_record_format_error:
        logger.error('In Record:\n%s', record)
    elif is_record_format_warning:
        logger.warning('In Record:\n%s', record)
    elif is_record_format_info:
        logger.info('In Record:\n%s', record)
    elif is_record_format_debugging:
        logger.debug('In Record:\n%s', record)

    logger.info('%s record error(s) found.', record_error_no)
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
    global file_error_no

    with open(input_path, 'rb') as input_file:
        with open(output_path, 'wb') as output_file:
            reader = MARCReader(input_file, force_utf8=True)
            writer = MARCWriter(output_file)

            for record in reader:
                record = link_bibliographic_headings_to_koha_authority_ids(record, mapping)
                record = prepare_holding_data(record)
                # TODO: instead of deleting 999, move to different fields/subfields
                record.remove_fields('999')
                file_error_no += record_error_no
                writer.write(record)


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
            file_error_no = 0
            without_extension = os.path.splitext(filename)[0]
            logger.info("Processing file '%s' ...", filename)
            process_bibliographic_data(
                input_directory + '/' + filename,
                output_directory + without_extension + '-preprocessed.mrc',
                authority_heading_to_authority_id_mapping
            )
            logger.info("Number of format errors in marc file: %s", file_error_no)
            logger.info("File '%s' processed.\n", filename)
            total_error_no += file_error_no

    logger.info("Holding field number maximum: %s (%s)", holding_field_max[1], holding_field_max[0])
    logger.info("Total number of record format errors: %s", total_error_no)
