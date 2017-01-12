#!/usr/bin/python
# -*- coding: utf-8 -*-

# This script filters duplicate authority data (based on field 001) and
# copies Aleph's internal control number to 035a (because 001 gets overwritten
# by Koha on import with its own control number).

from pymarc import MARCReader, Record, Field

import logging
import sys
import os

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def write_record(output_file, record):
    logger.debug('Writing authority with control number ' + str(record['001'].data))

    if record['035'] != None and record['035']['a'] != None:
        logger.debug('skipping record ' + str(record['001'] + ' it has'))
        logger.debug('field 035 a already set: ' + str(record['035']['a']))
    else:
        record.add_field(
            Field(
                tag = '035',
                indicators = [' ', ' '],
                subfields = [
                    'a', str(record['001'].data)
                ]))
        output_file.write(record.as_marc())

def run_filter(input_path, output_path):

    known_authorities = []
    duplicates_counter = 0

    # If target folder does not exist, create it.
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    with open(input_path, 'rb') as authority_file:

        with open(output_path, 'wb') as filtered_authority_file:
            reader = MARCReader(authority_file, force_utf8=True)
            for record in reader:
                if str(record['001']) in known_authorities:
                    duplicates_counter += 1
                else:
                    write_record(filtered_authority_file, record)
                    known_authorities.append(str(record['001']))

    logger.info(str(duplicates_counter) + ' duplicates found & filtered out.')

if __name__ == '__main__':
    if len(sys.argv) != 3:

        logger.info("Please provide as argument:")
        logger.info("1) Path to input file.")
        logger.info("2) Path/filename for filtered results.")

        sys.exit();

    run_filter(sys.argv[1], sys.argv[2])
