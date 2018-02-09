from pymarc import MARCReader

import logging
import sys
import os
import lib.mappings.library_keys as library_keys

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# This script currently the following purposes:
#   1) Mapping viable headings in the bibliographic data via String comparison (what Aleph also does internally)
#      to the authority data exported from Koha. In case of a match, Koha's interal authority ID gets
#      added to the bibliographic heading (subfield '9').
#   2) Library keys are mapped between Aleph and Koha. The keys got refactored in Koha, to add more naming consistency.

# AUTHORITY_CONTROL_FIELDS_MAPPING, read as:
#   ('marc  authority field number', 'marc bibliographic field number')
#   see also:
#   https://www.loc.gov/marc/authority/
#   https://www.loc.gov/marc/bibliographic/

AUTHORITY_CONTROL_FIELDS_MAPPING = [
    ('100', '100'), ('100', '600'), ('100', '700'),  # Personal Name
    ('110', '110'), ('110', '610'), ('110', '710'),  # Corporate Name
    ('111', '111'), ('111', '611'), ('111', '711'),  # Meeting Name
    ('130', '130'), ('130', '630'), ('130', '730'),  # Uniform Title
    ('150', '650'),                                  # Topical Term
    ('151', '651')                                   # Geographic Name
]


def create_mapping(file_path):
    new_mapping = {}
    with open(file_path, 'rb') as authority_file:
        reader = MARCReader(authority_file, force_utf8=True)
        for record in reader:
            for field in AUTHORITY_CONTROL_FIELDS_MAPPING:
                auth_field = field[0]
                if record[auth_field] is not None:
                    key = record[auth_field].as_marc('utf-8')
                    new_mapping[key] = record['001'].data

    return new_mapping


def update_authority_mapping(record, mapping):
    for field in AUTHORITY_CONTROL_FIELDS_MAPPING:
        for f in record.get_fields(field[1]):
            koha_id = mapping.get(f.as_marc('utf8'))
            if koha_id is not None:
                f.add_subfield('9', koha_id)

    return record


''' Koha expects the item information in field 952
* 952a: holding library
* 952b: owning library
* 952c: shelving location
'''


def update_library_and_site_key(record):
    for f in record.get_fields('952'):

        old_holding_library_key = None

        if 'a' in f:
            old_holding_library_key = str(f['a'])
            f['a'] = library_keys.map_aleph_key(old_holding_library_key)
        else:
            logger.debug('No holding library key found for record: ')
            logger.debug(str(record.as_json()))

        if 'b' in f:
            old_owning_library_key = str(f['b'])

            if old_holding_library_key is None:
                logger.debug('Setting owning library as holding library.')
                f.add_subfield('a', library_keys.map_aleph_key(old_owning_library_key))

            f['b'] = library_keys.map_aleph_key(old_owning_library_key)
        else:
            logger.debug('Setting holding library as owning library.')
            f.add_subfield('b', library_keys.map_aleph_key(old_holding_library_key))

        if 'a' not in f or 'b' not in f:
            logger.error('No valid library key for record: ')
            logger.error(str(record.as_json()))

        if 'c' in f:
            f['c'] = str(f['a']) + ' ' + str(f['c'])
        else:
            logger.warning('No shelving location for record:')
            logger.warning(' ' + str(record['001'].data))
            logger.warning(' field:')
            logger.warning(' ' + str(f))

    return record


def rewrite_bibliographic_data(input_path, output_path, mapping):
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    with open(input_path, 'rb') as input_file:
        with open(output_path, 'wb') as output_file:
            reader = MARCReader(input_file, force_utf8=True)
            for record in reader:

                record = update_authority_mapping(record, mapping)
                record = update_library_and_site_key(record)

                # TODO: instead of deleting 999, move to different fields/subfields
                record.remove_fields('999')
                output_file.write(record.as_marc())


if __name__ == '__main__':
    if len(sys.argv) != 4:

        logger.info("Please provide as argument:")
        logger.info("1) Path to bibliograhic data export from Aleph.")
        logger.info("2) Path to authority data export from Koha.")
        logger.info("3) Path/filename for filtered results.")
        sys.exit()

    rewrite_bibliographic_data(sys.argv[1], sys.argv[3], create_mapping(sys.argv[2]))
