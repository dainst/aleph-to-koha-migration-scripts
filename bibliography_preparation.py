from pymarc import MARCReader, Record, Field

import logging
import sys
import os

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def create_mapping(file_path):
    mapping = {}
    with open(file_path, 'rb') as authority_file:
        reader = MARCReader(authority_file, force_utf8=True)
        for record in reader:
            mapping[record['035']['a']] = record['001'].data
            
    return mapping

if __name__ == '__main__':
    if len(sys.argv) != 4:

        logger.info("Please provide as argument:")
        logger.info("1) Path to bibliograhic export from Aleph.")
        logger.info("2) Path to authority export from Koha.")
        logger.info("3) Path/filename for filtered results.")
        sys.exit()

    create_mapping(sys.argv[2])
    # load bibliographic data
        # preprocess
        # update control number to koha's via mapping
