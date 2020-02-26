from pymarc import MARCReader, MARCWriter, Field, parse_xml_to_array

import logging
import os
import sys
import pickle

import lib.mappings.marc_mappings as marc_mappings
import lib.marc_bibliographic.holdings as holdings
import lib.marc_bibliographic.thesaurus as thesaurus

from lib.marc_bibliographic.gazetteer import GazetteerThesaurusMapper

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
gazetteer_mapper = GazetteerThesaurusMapper()


def link_bibliographic_data_to_koha_authority_ids(bibliographic_record,
                                                  heading_to_authority_id_mapping,
                                                  gazetteer_id_to_authority_id_mapping):
    for field in marc_mappings.AUTHORITY_FIELDS_TO_BIBLIOGRAPHIC_FIELDS_MAPPING:
        for bibliographic_record_field in bibliographic_record.get_fields(field[1]):
            gazetteer_id = None

            if bibliographic_record_field.tag == '651' \
                    and bibliographic_record_field['2'] is not None\
                    and bibliographic_record_field['2'] in gazetteer_mapper.mapping:
                gazetteer_id = gazetteer_mapper.mapping[bibliographic_record_field['2']]

            # Fallback for Notations provided by Madrid
            # see: http://195.37.175.38/Record/000055439#details / https://gazetteer.dainst.org/app/#!/show/2074984
            if bibliographic_record_field.tag == '651' \
                        and bibliographic_record_field['2'] is not None \
                        and bibliographic_record_field['a'] is not None \
                        and f"{bibliographic_record_field['a'].strip()} {bibliographic_record_field['2'].strip()}" in gazetteer_mapper.mapping:
                gazetteer_id = gazetteer_mapper.mapping[f"{bibliographic_record_field['a'].strip()} {bibliographic_record_field['2'].strip()}"]

            if gazetteer_id is not None and gazetteer_id in gazetteer_id_to_authority_id_mapping:
                bibliographic_record_field.add_subfield('9', gazetteer_id_to_authority_id_mapping[gazetteer_id])
            else:
                koha_id = heading_to_authority_id_mapping.get(bibliographic_record_field['a'])
                if koha_id is not None:
                    bibliographic_record_field.add_subfield('9', koha_id)
                # Aleph does not only allow exact matches between headings, but is also able to match bibliographic
                # headings with one or more '.' to authority headings without any '.'. As a fallback, we try to match
                # again with the bibliographic heading stripped of all leading and trailing punctuation.
                else:
                    koha_id = heading_to_authority_id_mapping.get(bibliographic_record_field['a'].strip('.,- '))
                    if koha_id is not None:
                        bibliographic_record_field.add_subfield('9', koha_id)

    return bibliographic_record


def prepare_record_linking(record):
    if record['998'] is not None:

        for old_field in record.get_fields('998'):

            if 'a' in old_field and type(old_field['a']) == str:
                new_field = None
                if old_field['a'].strip() == 'ANA':
                    new_field = Field(tag='773', indicators=['0', '8'])
                elif old_field['a'].strip() == 'PAR':
                    new_field = Field(tag='776', indicators=['0', '8'])
                elif old_field['a'].strip() == 'UP':
                    new_field = Field(tag='787', indicators=['0', '8'])

                if new_field is not None:
                    if old_field['b'] is not None:
                        new_field.add_subfield('w', old_field['b'])
                    if old_field['n'] is not None:
                        new_field.add_subfield('t', old_field['n'])

                    record.add_field(new_field)
                    record.remove_field(old_field)

    return record


def split_summary_language_keys(record):

    field = record['041']

    if field is not None:
        if field['a'] is not None:
            split = [field['a'][i:i + 3] for i in range(0, len(field['a']), 3)]
            field.delete_subfield('a')
            for val in split:
                field.add_subfield('a', val)
        if field['b'] is not None:
            split = [field['b'][i:i + 3] for i in range(0, len(field['b']), 3)]
            field.delete_subfield('b')
            for val in split:
                field.add_subfield('b', val)

    return record


def process_bibliographic_data(input_path,
                               output_path,
                               authority_heading_to_authority_id_mapping,
                               gazetteer_id_to_authority_id_mapping):
    global file_record_count
    global file_error_count
    global estimated_sys_number_to_bibliographic_number_mapping

    kept_barcodes_count = 0
    deleted_barcodes_count = 0
    with open(input_path, 'rb') as input_file:
        with open(output_path, 'wb') as output_file:
            reader = MARCReader(input_file, force_utf8=True)
            writer = MARCWriter(output_file)

            for record in reader:
                if '001' not in record:
                    logger.error('Missing system number for ')
                    logger.error(record)
                    continue

                record_error_count = 0
                record = prepare_record_linking(record)
                record = split_summary_language_keys(record)

                error_count, kept_count, deleted_count = holdings.prepare_marc(record)

                kept_barcodes_count += kept_count
                deleted_barcodes_count += deleted_count

                record_error_count += error_count
                record_error_count += thesaurus.prepare_marc(record)

                record = link_bibliographic_data_to_koha_authority_ids(record,
                                                                       authority_heading_to_authority_id_mapping,
                                                                       gazetteer_id_to_authority_id_mapping)

                if record['003'] is None:
                    record.add_field(Field(tag='003', data="DE-2553"))
                if record['040'] is None:
                    record.add_field(Field(
                        tag=40, indicators=(' ', ' '), subfields=[
                            'a', 'DE-2553',
                            'c', 'DE-2553'
                        ])
                    )

                estimated_sys_number_to_bibliographic_number_mapping[record['001'].data] = file_record_count + 1
                writer.write(record)
                file_record_count += 1

                file_error_count += record_error_count

    logger.info(f'Kept {kept_barcodes_count} barcodes, removed {deleted_barcodes_count}.')


def create_authority_data_to_authority_id_mapping(file_path):
    logger.info('Creating authority-heading-to-authority-id mapping based on exported authority data...')

    heading_to_authority_id_mapping = {}
    gazetteer_id_to_authority_id_mapping = {}
    with open(file_path, 'rb') as authority_file:
        reader = parse_xml_to_array(authority_file)
        for authority_record in reader:
            for field in marc_mappings.AUTHORITY_FIELDS_TO_BIBLIOGRAPHIC_FIELDS_MAPPING:
                auth_field = field[0]
                if authority_record[auth_field] is not None:

                    authority_heading = authority_record[auth_field]['a']
                    authority_id = authority_record['001'].data
                    heading_to_authority_id_mapping[authority_heading] = authority_id

                    if auth_field == '151' \
                            and authority_record['024'] is not None \
                            and authority_record['024']['2'] == 'iDAI.gazetteer':

                        gazetteer_id = authority_record['024']['a']
                        gazetteer_id_to_authority_id_mapping[gazetteer_id] = authority_id

    logger.info('Done.\n')

    return heading_to_authority_id_mapping, gazetteer_id_to_authority_id_mapping


if __name__ == '__main__':

    total_record_count = 0
    total_error_count = 0

    if len(sys.argv) != 4:
        logger.info("Please provide as argument:")
        logger.info("1) Path to bibliograhic data (directory) exports from Aleph.")
        logger.info("2) Path to authority data (file) export from Koha.")
        logger.info("3) Path to output directory for results.")
        sys.exit()

    authority_heading_to_authority_id_mapping, gazetteer_id_to_authority_id_mapping = \
        create_authority_data_to_authority_id_mapping(sys.argv[2])
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
                authority_heading_to_authority_id_mapping,
                gazetteer_id_to_authority_id_mapping
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
