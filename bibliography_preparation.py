from pymarc import MARCReader, MARCWriter

import logging
import sys
import os

import lib.database_connections.mariadb as mariadb
import lib.mappings.library_keys as library_keys
import lib.mappings.marc_mappings as marc_mappings
import lib.oracle_helper.dates as dates_helper

# This script currently serves the following purposes:
#   1) Mapping viable headings in the bibliographic data via String comparison (what Aleph also does internally)
#      to the authority data exported from Koha. In case of a match, Koha's internal authority ID gets
#      added to the bibliographic heading (subfield '9').
#   2) Library keys are mapped between Aleph and Koha. The keys got refactored in Koha, to add more naming consistency.

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING = None


def map_item_type(marc_field_952):
    if 'y' in marc_field_952:
        aleph_material_key = str(marc_field_952['y'])
        item_type = marc_mappings.map_material(aleph_material_key)
    else:
        item_type = None
        logger.error('No marc subfield 952y found!')

    return item_type


def map_call_number(marc_field_952):
    if 'o' in marc_field_952:
        call_number = marc_field_952['o']
    else:
        call_number = None

    return call_number


def map_aleph_vendor_code(aleph_z70_vendor_code):
    for (aleph_code, koha_id) in ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING:
        #logger.info("aleph_code: %s", aleph_code)
        #logger.info("koha_id: %s", koha_id)
        if aleph_z70_vendor_code == aleph_code:
            return koha_id
    else:
        return ''


def map_source_of_acquisition(marc_field_952):
    if 'e' in marc_field_952:
        source_of_acquisition = marc_field_952['e']
        if source_of_acquisition is not None:
            #logger.info("Aleph vendor code: %s", source_of_acquisition)
            source_of_acquisition = map_aleph_vendor_code(source_of_acquisition)
            #logger.info("Koha bookseller name: %s", source_of_acquisition)
    else:
        source_of_acquisition = None

    return source_of_acquisition


def map_date_acquired(marc_field_952):
    if 'd' in marc_field_952:
        date_acquired = dates_helper.process_aleph_date(marc_field_952['d'])
    else:
        date_acquired = None

    return date_acquired


def create_shelving_key(library_key, shelving_key):
    return library_key + ' ' + shelving_key


def map_shelving_location_code(marc_field_952):
    owning_library_key = marc_field_952['a']

    if 'c' in marc_field_952:
        shelving_location_code = create_shelving_key(owning_library_key, marc_field_952['c'])
    else:
        logger.debug('No marc subfield 952c found!')
        logger.debug('Copy subfield 952a in subfield 952c ...')
        shelving_location_code = owning_library_key
        marc_field_952.add_subfield('c', shelving_location_code)
        logger.debug('Subfield 952c = %s', marc_field_952['c'])

    return shelving_location_code


def map_holding_library(marc_field_952):
    if 'b' in marc_field_952:
        holding_library_key = library_keys.map_aleph_key(marc_field_952['b'])
    else:
        holding_library_key = None
        logger.error('No marc subfield 952b found!')

    return holding_library_key


def map_owning_library(marc_field_952):
    if 'a' in marc_field_952:
        owning_library_key = library_keys.map_aleph_key(marc_field_952['a'])
    else:
        owning_library_key = None
        logger.error('No marc subfield 952a found!')

    return owning_library_key


def check_required_subfields(marc_field_952):
    is_successful = False

    if all(subfields not in marc_field_952 for subfields in ('a', 'b')) or 'y' not in marc_field_952:
        logger.error('Neither marc subfield 952a and 952b found nor subfield 952y!')
    elif 'a' and 'b' not in marc_field_952:
        if 'a' not in marc_field_952:
            logger.debug('No marc subfield 952a found!')
            logger.debug('Copy subfield 952b in subfield 952a ...')
            marc_field_952.add_subfield('a', marc_field_952['b'])
            logger.debug('Subfield 952a = %s', marc_field_952['a'])
        if 'b' not in marc_field_952:
            logger.debug('No marc subfield 952b found!')
            logger.debug('Copy subfield 952a in subfield 952b ...')
            marc_field_952.add_subfield('b', marc_field_952['a'])
            logger.debug('Subfield 952b = %s', marc_field_952['b'])

        is_successful = True
    else:
        is_successful = True

    return is_successful


def prepare_holding_data(record):
    logger.debug('Processing holding information of Marc record: %s ...', record.leader)
    is_record_format_error = False
    is_record_format_warning = False
    is_record_format_info = False

    for marc_field_952 in record.get_fields('952'):

        # TODO Datentypen und Feldlängen überprüfen!
        if check_required_subfields(marc_field_952):

            # '952$a' Owning Library (required by Koha)
            koha_owning_library = map_owning_library(marc_field_952)
            if koha_owning_library is not None:
                marc_field_952['a'] = koha_owning_library
            else:
                logger.error('No valid owning library key found: 952$a = "%s"', marc_field_952['a'])
                logger.error('Skipping field: %s', marc_field_952)
                record.remove_field(marc_field_952)
                is_record_format_error = True
                continue


            # '952$b' Holding library (required by Koha)
            koha_holding_library = map_holding_library(marc_field_952)
            if koha_holding_library is not None:
                marc_field_952['b'] = koha_holding_library
            else:
                logger.error('No valid holding library key found: 952$b = "%s"', marc_field_952['b'])
                logger.error('Skipping field: %s', marc_field_952)
                record.remove_field(marc_field_952)
                is_record_format_error = True
                continue

            # '952$c' Shelving location code
            koha_shelving_location = map_shelving_location_code(marc_field_952)
            if koha_shelving_location is not None:
                marc_field_952['c'] = koha_shelving_location
            else:
                logger.info('No valid shelving location found: 952$c = "%s"', marc_field_952['c'])
                logger.info('Skipping subfield "c" in marc field %s', marc_field_952)
                #marc_field_952['c'] = ''
                is_record_format_info = True

            # '952$d' Date acquired
            koha_date_acquired = map_date_acquired(marc_field_952)
            if koha_date_acquired is not None:
                marc_field_952['d'] = koha_date_acquired
            else:
                logger.info('No valid "date aquired" found: 952$d = "%s"', marc_field_952['d'])
                logger.info('Skipping subfield "d" in marc field %s', marc_field_952)
                #marc_field_952['d'] = ''
                is_record_format_info = True

            # '952$e' Source of acquisition
            koha_source_of_acquisition = map_source_of_acquisition(marc_field_952)
            if koha_source_of_acquisition is not None:
                #logger.info("Koha source of acquisition: %s", koha_source_of_acquisition)
                marc_field_952['e'] = koha_source_of_acquisition
            else:
                logger.info('No valid "source of aquisition" found: 952$e = "%s"', marc_field_952['e'])
                logger.info('Skipping subfield "e" in marc field %s', marc_field_952)
                #marc_field_952['e'] = ''
                is_record_format_info = True

            # '952$g' Purchase price
            # '952$h' Serial enumeration

            # '952$o' Koha full call number
            koha_call_number = map_call_number(marc_field_952)
            if koha_call_number is not None:
                marc_field_952['o'] = koha_call_number
            else:
                logger.info('No valid "call number" found: 952$o = "%s"', marc_field_952['o'])
                logger.info('Skipping subfield "o" in marc field %s', marc_field_952)
                #marc_field_952['o'] = ''
                is_record_format_info = True

            # '952$p' Barcode (required for circulation)
            # '952$t' Copy number
            # '952$u' Uniform Resource Identifier
            # '952$v' Replacement price
            # '952$w' Price effective from
            # '952$x' Nonpublic note

            # '952$y' Item type (required by Koha)
            koha_item_type = map_item_type(marc_field_952)
            if koha_item_type is not None:
                marc_field_952['y'] = koha_item_type
            else:
                logger.error('No valid item type found: 952$y = "%s"', marc_field_952['y'])
                logger.error('Skipping field: %s', marc_field_952)
                record.remove_field(marc_field_952)
                is_record_format_error = True
                continue

            # '952$z' Public note
            # '952$0' Withdrawn status
            # '952$1' Lost status
            # '952$2' Classification
            # '952$3' Materials specified
            # '952$4' Damaged status
            # '952$5' Use restrictions
            # '952$7' Not for loan
            # '952$8' Collection code
            # '952$9' Item number

        else:
            logger.error('Skipping field: %s', marc_field_952)
            record.remove_field(marc_field_952)
            is_record_format_error = True

    if is_record_format_error:
        logger.error('In Record:\n%s', record)
    elif is_record_format_warning:
        logger.warning('In Record:\n%s', record)
    elif is_record_format_info:
        logger.info('In Record:\n%s', record)

    logger.debug("Marc Record '%s' process completed!\n", record.leader)

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

    return result


def process_bibliographic_data(input_path, output_path, mapping):
    global ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING
    ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING = get_aleph_vendor_code_koha_bookseller_name_mapping()
    logger.info("ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING:\n%s", ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING)

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

    counter = 0
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
            counter += 1
