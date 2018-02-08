from pymarc import MARCReader

import logging
import sys
import os
import lib.mappings.library_keys as library_keys

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
    ('100', '100'), ('100', '600'), ('100', '700'), # Personal Name
    ('110', '110'), ('110', '610'), ('110', '710'), # Corporate Name
    ('111', '111'), ('111', '611'), ('111', '711'), # Meeting Name
    ('130', '130'), ('130', '630'), ('130', '730'), # Uniform Title
    ('150', '650'),                                 # Topical Term
    ('151', '651')                  # Geographic Name
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


def update_library_and_site_key(record):
    for f in record.get_fields('952'):
        if f['a'] is not None:
            old_key = str(f['a'])
            f['a'] = library_keys.map_aleph_key(old_key)
            if f['c'] is not None:
                old_site = str(f['c'])
                f['c'] = old_site.replace(old_key, library_keys.map_aleph_key(old_key), 1)

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

                output_file.write(record.as_marc())


if __name__ == '__main__':
    if len(sys.argv) != 4:

        logger.info("Please provide as argument:")
        logger.info("1) Path to bibliograhic data export from Aleph.")
        logger.info("2) Path to authority data export from Koha.")
        logger.info("3) Path/filename for filtered results.")
        sys.exit()

    rewrite_bibliographic_data(sys.argv[1], sys.argv[3], create_mapping(sys.argv[2]))
