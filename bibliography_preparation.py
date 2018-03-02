from pymarc import MARCReader, MARCWriter

import logging
import sys
import os
import lib.mappings.library_keys as library_keys
import lib.mappings.marc_mappings as marc_mappings

# This script currently serves the following purposes:
#   1) Mapping viable headings in the bibliographic data via String comparison (what Aleph also does internally)
#      to the authority data exported from Koha. In case of a match, Koha's interal authority ID gets
#      added to the bibliographic heading (subfield '9').
#   2) Library keys are mapped between Aleph and Koha. The keys got refactored in Koha, to add more naming consistency.

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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


def link_bibliographic_headings_to_koha_authority_ids(bibliographic_record, heading_to_authority_id_mapping):
    for field in marc_mappings.AUTHORITY_FIELDS_TO_BIBLIOGRAPHIC_FIELDS_MAPPING:
        for bibliographic_record_field in bibliographic_record.get_fields(field[1]):
            koha_id = heading_to_authority_id_mapping.get(bibliographic_record_field.as_marc('utf8'))
            if koha_id is not None:
                bibliographic_record_field.add_subfield('9', koha_id)

    return bibliographic_record


def create_shelving_key(library_key, shelving_key):
    return library_key + ' ' + shelving_key


# MARC holds location information in field 852.
# Koha expects the item information in field 952:
# * 952a: holding library
# * 952b: owning library
# * 952c: shelving location


def update_library_and_shelving_location_keys(record):
    # TODO: 852b and c are repeatable, assignment does not work like this
    # for f in record.get_fields('852'):
    #     if 'b' in f:
    #         old_sublocation = f['b']
    #         f['b'] = library_keys.map_aleph_key(str(old_sublocation))
    #
    #         if 'c' in f:
    #             f['c'] = create_shelving_key(str(f['b']), str(f['c']))

    for f in record.get_fields('952'):

        old_holding_library_key = str(f['a'])
        new_holding_library_key = library_keys.map_aleph_key(old_holding_library_key)

        if new_holding_library_key is None:
            logger.error('No valid holding library key found in field 952 a:')
            logger.error(f)
            logger.error('In Record:')
            logger.error(record)
            logger.error('Skipping...')
            continue

        f['a'] = new_holding_library_key

        if 'b' in f:
            old_owning_library_key = f['b']
            new_owning_library_key = library_keys.map_aleph_key(old_owning_library_key)

            if new_owning_library_key is None:
                logger.error('No valid owning library key found in field 952 b:')
                logger.error(f)
                logger.error('In Record:')
                logger.error(record)
                logger.error('Using 952 a')

                f['b'] = new_holding_library_key
            else:
                f['b'] = new_owning_library_key
        else:
            f.add_subfield('b', new_holding_library_key)

        if 'c' in f:
            f['c'] = create_shelving_key(new_holding_library_key, str(f['c']))
        else:
            f.add_subfield('c', new_holding_library_key)
            logger.debug('No shelving location found in field 952 c:')
            logger.debug(f)
            logger.debug('Record:')
            logger.debug(record)
            logger.debug('Value set to value in 952 a.')

    return record


def update_material_type(record):
    for f in record.get_fields('952'):
        if 'y' in f:
            aleph_material_key = str(f['y'])
            f['y'] = marc_mappings.map_material(aleph_material_key)

    return record


def process_bibliographic_data(input_path, output_path, mapping):

    with open(input_path, 'rb') as input_file:
        with open(output_path, 'wb') as output_file:
            reader = MARCReader(input_file, force_utf8=True)
            writer = MARCWriter(output_file)
            for record in reader:

                record = link_bibliographic_headings_to_koha_authority_ids(record, mapping)
                record = update_library_and_shelving_location_keys(record)
                record = update_material_type(record)
                # TODO: instead of deleting 999, move to different fields/subfields
                record.remove_fields('999')
                writer.write(record)

            reader.close()
            writer.close()


if __name__ == '__main__':
    if len(sys.argv) != 4:

        logger.info("Please provide as argument:")
        logger.info("1) Path to bibliograhic data (directory) exports from Aleph.")
        logger.info("2) Path to authority data (file) export from Koha.")
        logger.info("3) Path to output directory for results.")
        sys.exit()

    heading_to_authority_id_mapping = create_authority_heading_to_authority_id_mapping(sys.argv[2])

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
            logger.info('Processing file ' + filename)
            process_bibliographic_data(input_directory + '/' + filename,
                                       output_directory + without_extension + '-preprocessed.mrc',
                                       heading_to_authority_id_mapping)
            counter += 1

