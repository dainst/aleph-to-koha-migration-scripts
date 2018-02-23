#!/usr/bin/python
# -*- coding: utf-8 -*-

# This script filters duplicate authority data (based on field 001) and
# copies Aleph's internal control number to 035a (because 001 gets overwritten
# by Koha on import with its own control number).

from pymarc import MARCReader, Field

import logging
import sys
import os
import re

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# zum TOP: Feld 010:
# Korrekte Muster in Feld 010 (basierend auf LC authority record prefixes:
# n - for name headings (Bsp.: n 2001040831 und n96002922); LC
# nb - for name headings ; British Library (Bsp.: nb 90633208 und nb2001067313)
# no - for name headings ; OCLC (Bsp.: no 00003545 und no2010088353)

LC_CONTROL_NUMBER_STRUCTURE_A_PATTERN = re.compile(r'^([a-z]{1,3})(\s{0,2})([0-9]{8})(.?)$', re.IGNORECASE)
LC_CONTROL_NUMBER_STRUCTURE_B_PATTERN = re.compile(r'^([a-z]{1,2})(\s{0,1})([0-9]{10})$', re.IGNORECASE)

# Make sure the LoC numbers are formatted correctly

def fix_loc_number(record):
    loc_data = record['010']

    if loc_data is None:
        return record

    if 'a' not in loc_data:
        record.remove_field(loc_data)

        logger.debug('Removed field 010, because there is no subfield a:')
        logger.debug(loc_data)
        logger.debug('Updated record:')
        logger.debug(record)
        return record

    match_structure_a = re.match(LC_CONTROL_NUMBER_STRUCTURE_A_PATTERN, loc_data['a'])
    match_structure_b = re.match(LC_CONTROL_NUMBER_STRUCTURE_B_PATTERN, loc_data['a'])

    updated_field = ' ' * 12

    if match_structure_a is not None:
        alphabetic_prefix = match_structure_a.group(1)
        numbers = match_structure_a.group(3)
        supplement_number = match_structure_a.group(4)

        updated_field = alphabetic_prefix + updated_field[len(alphabetic_prefix):]
        updated_field = updated_field[:3] + numbers

        if supplement_number.isdigit():
            updated_field = updated_field[:11] + supplement_number
        else:
            updated_field = updated_field[:11] + ' '

        # TODO remove hack, added to enable the script to finish, the datasets have multiple subfields a
        if record['001'].data == '000105336' or record['001'].data == '000131634':
            record.remove_field(loc_data)
            return record

        record['010']['a'] = updated_field
        return record

    if match_structure_b is not None:
        alphabetic_prefix = match_structure_b.group(1)
        numbers = match_structure_b.group(3)

        # Numbers 0:4 should be a year in structure B, remove field if that is not the case
        if numbers[0:2] != '20' and numbers[0:2] != '19':
            record.remove_field(loc_data)

            logger.warning('Removed field 010, because year seems invalid: ' + numbers[0:4])
            logger.warning(loc_data)
            logger.warning(record)
            return record

        updated_field = alphabetic_prefix + updated_field[len(alphabetic_prefix):]
        updated_field = updated_field[:2] + numbers

        if len(updated_field) != 12:
            record.remove_field(loc_data)

            logger.warning('Removed original field 010, because updated field is too long: ')
            logger.warning(updated_field)
            logger.warning(record)

            return record

        record['010']['a'] = updated_field
        return record

    record.remove_field(loc_data)
    return record


def filter_cataloging_sources(record):

    valid_cataloging_agencies = [
        'ATLA', 'BAV', 'BNI', 'BSA', 'CaQMCCA', 'CCSC', 'CFCPL', 'CLU', 'CoU', 'CSt', 'CtY', 'CU', 'D.O.C.', 'DFG',
        'DGU', 'DGPO', 'DGW', 'DHMM', 'DJBF', 'DLC', 'DSI-F', 'DSI', 'FMU', 'FTaSU', 'FU', 'GBV', 'GEU', 'GU', 'HkUST',
        'Hollis Catalog', 'IAhCCS', 'IaU', 'ICA', 'ICIU', 'ICRL', 'ICU', 'IeDuTC', 'IEN', 'InU', 'ItFiC', 'LoC', 'LOC',
        'MBU-T', 'MCM', 'MdU', 'MeLB', 'MH', 'MH-FA', 'MH-P', 'MiU', 'MnU', 'MoSR', 'MoKU', 'MoSU-L', 'MoSW', 'MOU',
        'MWiCA', 'MX-', 'NAnB-G', 'NBuU', 'NcD', 'NcU', 'NIC', 'NjP', 'NNC', 'NNC-EA', 'NNFr', 'NNMM', 'NN-PD', 'NNPM',
        'NNU', 'OCI', 'OCLC', 'OCIMA', 'OCoLC', 'OCIW', 'ODaU', 'OGND', 'OkU', 'PE-LiPUB', 'PE-LiPUR', 'PPiU', 'PU',
        'RPB', 'SaFITSA', 'SaPrNL', 'SaPRUSA', 'ScU', 'SdMadT', 'STEdNL', 'TNJ', 'TxCM', 'Uk', 'UkCU', 'UkOxU', 'UPB',
        'VIAF', 'ViU', 'TxU'
    ]

    cataloging_source = record['040']
    if cataloging_source is None:
        return record

    if 'a' not in cataloging_source:
        record.remove_field(cataloging_source)

        logger.debug('Removed field 040, because there is no subfield a:')
        logger.debug(cataloging_source)
        logger.debug('Updated record:')
        logger.debug(record)
        return record

    if str(cataloging_source['a']) not in valid_cataloging_agencies:
        record.remove_field(cataloging_source)
        logger.debug('Removed field 040, subfield a is no valid cataloging agency:')
        logger.debug(cataloging_source)
        logger.debug('Updated record:')
        logger.debug(record)
        return record

    return record


def process_records(input_path, output_path):

    # If target folder does not exist, create it.
    if not os.path.exists(os.path.dirname(output_path)) and os.path.dirname(output_path) != '':
        os.makedirs(os.path.dirname(output_path))

    with open(input_path, 'rb') as authority_file, open(output_path, 'wb') as output_file:
        reader = MARCReader(authority_file, force_utf8=True)
        for record in reader:
            record = fix_loc_number(record)
            record = filter_cataloging_sources(record)
            output_file.write(record.as_marc())


if __name__ == '__main__':
    if len(sys.argv) != 3:

        logger.info("Please provide as argument:")
        logger.info("1) Path to input file.")
        logger.info("2) Path/filename for filtered results.")

        sys.exit()

    process_records(sys.argv[1], sys.argv[2])

