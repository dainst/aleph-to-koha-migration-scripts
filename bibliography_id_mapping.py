from pymarc import MARCReader

import pickle
import logging
import os
import sys

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


SYS_NUMBER_TO_BIB_ID_MAPPING = dict()


def create_mapping(input_path):
    global SYS_NUMBER_TO_BIB_ID_MAPPING

    with open(input_path, 'rb') as input_file:
        reader = MARCReader(input_file, force_utf8=True)

        for record in reader:
            if '001' not in record:
                logger.error('Record without 001 value: ')
                logger.error(record.as_dict())
                continue

            SYS_NUMBER_TO_BIB_ID_MAPPING[record['001'].data] = record['999']['c']


def write_mapping():
    global SYS_NUMBER_TO_BIB_ID_MAPPING

    output_path = './pickles/'

    if not os.path.exists(os.path.dirname(output_path)) and os.path.dirname(output_path) != '':
        os.makedirs(os.path.dirname(output_path))

    with open(output_path + 'SYS_NUMBER_TO_BIB_ID_MAPPING.pickle', 'wb') as output_file:
        pickle.dump(SYS_NUMBER_TO_BIB_ID_MAPPING, output_file)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Path to bibliographic data (directory) exports from Koha.')
        sys.exit()

    input_directory = sys.argv[1]

    if not os.path.dirname(input_directory).endswith('/'):
        input_directory += '/'

    for filename in os.listdir(input_directory):
        logger.info('Reading file %s.' % filename)
        if filename.endswith('.mrc'):
            create_mapping(input_directory + filename)

    write_mapping()
