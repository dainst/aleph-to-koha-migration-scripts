from pymarc import MARCReader, MARCWriter, Field

import logging
import os
import sys
import pickle

import lib.mappings.marc_mappings as marc_mappings
import lib.marc_bibliographic.holdings as holdings
import lib.marc_bibliographic.thesaurus as thesaurus

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

estimated_sys_number_to_bibliographic_number_mapping = dict()


def link_bibliographic_headings_to_koha_authority_ids(bibliographic_record, heading_to_authority_id_mapping):
    for field in marc_mappings.AUTHORITY_FIELDS_TO_BIBLIOGRAPHIC_FIELDS_MAPPING:
        for bibliographic_record_field in bibliographic_record.get_fields(field[1]):
            koha_id = heading_to_authority_id_mapping.get(bibliographic_record_field.as_marc('utf8'))

            if koha_id is not None:
                bibliographic_record_field.add_subfield('9', koha_id)

    return bibliographic_record


def prepare_record_linking(record):
    if record['998'] is not None:

        for old_field in record.get_fields('998'):
            new_field = Field(tag='773', indicators=['\\', '\\'])

            if old_field['b'] is not None:
                new_field.add_subfield('w', old_field['b'])
            if old_field['m'] is not None:
                new_field.add_subfield('t', old_field['m'])

            record.add_field(new_field)
            record.remove_field(old_field)

    return record


def process_bibliographic_data(input_path, output_path, mapping):
    global file_record_count
    global file_error_count
    global estimated_sys_number_to_bibliographic_number_mapping

    with open(input_path, 'rb') as input_file:
        with open(output_path, 'wb') as output_file:
            reader = MARCReader(input_file, force_utf8=True)
            writer = MARCWriter(output_file)

            for record in reader:
                record_error_count = 0
                record = link_bibliographic_headings_to_koha_authority_ids(record, mapping)
                record = prepare_record_linking(record)
                record_error_count += holdings.prepare_marc(record)
                record_error_count += thesaurus.prepare_marc(record)

                if record['001'] is not None:
                    estimated_sys_number_to_bibliographic_number_mapping[record['001'].data] = file_record_count + 1
                    writer.write(record)
                    file_record_count += 1
                else:
                    logger.error('No system number 001 for record:')
                    logger.error(record)
                file_error_count += record_error_count


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

    logger.info('Done.\n')

    return result


if __name__ == '__main__':

    total_record_count = 0
    total_error_count = 0

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

    sorted_files = os.listdir(input_directory)
    sorted_files = sorted(sorted_files)

    for filename in sorted_files:
        if filename.endswith('.mrc'):

            file_record_count = 0
            file_error_count = 0
            without_extension = os.path.splitext(filename)[0]
            logger.info("Processing file '%s' ...", filename)
            process_bibliographic_data(
                input_directory + '/' + filename,
                output_directory + without_extension + '-preprocessed.mrc',
                authority_heading_to_authority_id_mapping
            )
            total_record_count += file_record_count
            total_error_count += file_error_count
            logger.info("Number of records in marc file: %s", file_record_count)
            logger.info("Number of record errors in marc file: %s", file_error_count)

            logger.info("File '%s' processed.\n", filename)

    logger.info(
        "Holding field number maximum: %s (in: '%s')", holdings.holding_field_max[1], holdings.holding_field_max[0])
    logger.info("Total number of record errors: %s", total_error_count)
    logger.info("Total number of records: %s", total_record_count)

    with open('./pickles/estimated_sys_number_to_bibliographic_number_mapping.pickle', 'wb') as mapping_file:
        pickle.dump(estimated_sys_number_to_bibliographic_number_mapping, mapping_file)
