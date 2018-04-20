from pymarc import MARCReader

import pickle
import logging
import os
import sys

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


ID_MAPPING = dict()


def create_mapping(input_path):
    global ID_MAPPING

    with open(input_path, 'rb') as input_file:
        reader = MARCReader(input_file, force_utf8=True)

        for record in reader:
            field_952_list = record.get_fields('952')
            for field in field_952_list:
                if 'W' in field and 'V' in field:
                    z30_rec_key = field['W']+field['V']
                    koha_bib_id = record['999']['c']

                    if z30_rec_key in ID_MAPPING:
                        logger.error('%s already present in mapping! This should not happen.' % z30_rec_key)
                        logger.error('Existing mapping Zenon-ID: %s, Koha-ID: %s'
                                     % (ID_MAPPING[z30_rec_key]['zenon_id'], ID_MAPPING[z30_rec_key]['koha_id']))
                        logger.error('Current mapping Zenon-ID: %s, Koha-ID: %s'
                                     % (record['001'].data, koha_bib_id))
                        continue

                    ID_MAPPING[z30_rec_key] = {
                        'zenon_id': record['001'].data,
                        'koha_id': koha_bib_id
                    }


def write_mapping(output_filepath):
    global ID_MAPPING

    logger.info('Pickling mapping data at %s.' % output_filepath)
    if not os.path.exists(os.path.dirname(output_filepath)) and os.path.dirname(output_filepath) != '':
        os.makedirs(os.path.dirname(output_filepath))

    with open(output_filepath, 'wb') as output_file:
        pickle.dump(ID_MAPPING, output_file)


if __name__ == '__main__':

    if len(sys.argv) != 3:
        logger.info('Please provide as argument:')
        logger.info('1) Path to bibliograhic data (directory) exports from Koha.')
        logger.info('2) File path for the result (Python pickle).')
        sys.exit()

    input_directory = sys.argv[1]
    for filename in os.listdir(input_directory):
        logger.info('Reading file %s.' % filename)
        if filename.endswith('.mrc'):
            create_mapping(input_directory + filename)

    write_mapping(sys.argv[2])
