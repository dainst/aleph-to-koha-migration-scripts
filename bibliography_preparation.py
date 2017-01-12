from pymarc import MARCReader, Record, Field

import logging
import sys
import os

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

RELEVANT_AUTHORITY_CONTROL_FIELDS = ['100', '110', '111', '130']

def create_mapping(file_path):
    mapping = {}
    with open(file_path, 'rb') as authority_file:
        reader = MARCReader(authority_file, force_utf8=True)
        for record in reader:
            for field in RELEVANT_AUTHORITY_CONTROL_FIELDS:
                if record[field] != None:
                    mapping[record[field].as_marc('utf-8')] = record['001'].data

    return mapping

def rewrite_bibliographic_data(input_path, output_path, mapping):
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    with open(input_path, 'rb') as input_file:
        with open(output_path, 'wb') as output_file:
            reader = MARCReader(input_file, force_utf8=True)
            for record in reader:
                for field in RELEVANT_AUTHORITY_CONTROL_FIELDS:
                    if(record[field] != None):
                        kohaID = mapping.get(record[field].as_marc('utf8'))
                        if kohaID != None:
                            record[field].add_subfield('9', kohaID)
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
