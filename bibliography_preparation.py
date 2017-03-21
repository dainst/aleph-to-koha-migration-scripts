from pymarc import MARCReader, Record, Field

import logging
import sys
import os

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

# LIBRARY_KEY_MAPPING
#   Mapping of old library keys in Aleph to the refactored ones in Koha.

LIBRARY_KEY_MAPPING = {
    'BAYS':  'BASSM',
    'BSA':   'BBSA',
    'WINCK': 'BWINCK',
    'ZADAR': 'BICUAZ',
    'ATHEN': 'DAIA',
    'EURAS': 'DAIE',
    'DAI':   'DAIG',
    'ISTAN': 'DAII',
    'BONN':  'DAIB',
    'KAIRO': 'DAIK',
    'MADRD': 'DAIM',
    'ORIEN': 'DAIO',
    'RGK':   'DAIF',
    'ROM':   'DAIR',
    'ZENTR': 'DAIZ',
    'DAMAS': 'DAID',
    'PEK':   'DAIP',
    'SANAA': 'DAIS',
    'TEHER': 'DAIT',
    'DEIA':  'DEAI',
    'DEIJ':  'DEIJ',
    'LUBL':  'BIAUL',
    'SCHW':  'BLDMV'
}

def create_mapping(file_path):
    mapping = {}
    with open(file_path, 'rb') as authority_file:
        reader = MARCReader(authority_file, force_utf8=True)
        for record in reader:
            for field in AUTHORITY_CONTROL_FIELDS_MAPPING:
                auth_field = field[0]
                if record[auth_field] != None:
                    key = record[auth_field].as_marc('utf-8')
                    mapping[key] = record['001'].data

    return mapping


def update_authority_mapping(record):
    for field in AUTHORITY_CONTROL_FIELDS_MAPPING:
        for f in record.get_fields(field[1]):
            koha_ID = mapping.get(f.as_marc('utf8'))
            if koha_ID != None:
                f.add_subfield('9', koha_ID)

    return record

def update_library_and_site_key(record):
    for f in record.get_fields('952'):
        if f['a'] != None:
            old_key = str(f['a'])
            f['a'] = LIBRARY_KEY_MAPPING[old_key]
            if f['c'] != None:
                old_site = str(f['c']);
                f['c'] = old_site.replace(old_key,
                    LIBRARY_KEY_MAPPING[old_key], 1)

    return record

def rewrite_bibliographic_data(input_path, output_path, mapping):
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    with open(input_path, 'rb') as input_file:
        with open(output_path, 'wb') as output_file:
            reader = MARCReader(input_file, force_utf8=True)
            for record in reader:

                record = update_authority_mapping(record)
                record = update_library_and_site_key(record)

                output_file.write(record.as_marc())

if __name__ == '__main__':
    if len(sys.argv) != 4:

        logger.info("Please provide as argument:")
        logger.info("1) Path to bibliograhic export from Aleph.")
        logger.info("2) Path to authority export from Koha.")
        logger.info("3) Path/filename for filtered results.")
        sys.exit()

    mapping = create_mapping(sys.argv[2])
    rewrite_bibliographic_data(sys.argv[1], sys.argv[3], mapping)
