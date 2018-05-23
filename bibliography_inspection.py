from pymarc import MARCReader

import logging
import os
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler = logging.FileHandler('./bibliography_inspection.log')
# file_handler.setLevel(logging.INFO)
# file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
logger.addHandler(console_handler)

file_record_no = 0
total_record_no = 0
file_error_no = 0
total_error_no = 0

field_952_A_no = 0
special_order_number_counter = 0


def inspect_order_numbers(record):
    global field_952_A_no
    global special_order_number_counter

    field_952_list = record.get_fields('952')
    for field_952 in field_952_list:
        field_952_A = field_952['A']

        if field_952_A is not None:
            field_952_A_no += 1

            if field_952_A == 'R/2005-397':
                special_order_number_counter += 1

            field_001_list = record.get_fields('001')
            for field_001 in field_001_list:
                logger.debug('%s: 952$A = %s', field_001, field_952_A)


field_300_e_and_3_comb_no = 0
field_300_e_no = 0
field_300_3_no = 0
field_852_3_no = 0
field_952_3_no = 0


def inspect_materials_specified_data(record):
    global field_300_e_no
    global field_300_3_no
    global field_300_e_and_3_comb_no
    global field_852_3_no
    global field_952_3_no

    field_952_list = record.get_fields('952')
    for field_952 in field_952_list:
        if field_952['y'] == 'MEDK':
            field_300_list = record.get_fields('300')
            for field_300 in field_300_list:
                if 'e' in field_300 or '3' in field_300:
                    field_001_list = record.get_fields('001')
                    if 'e' in field_300 and '3' in field_300:
                        field_300_e_and_3_comb_no += 1
                        for field_001 in field_001_list:
                            logger.debug('%s: 300$e = %s, 300$3 = %s', field_001, field_300['e'], field_300['3'])
                    elif 'e' in field_300:
                        field_300_e_no += 1
                        for field_001 in field_001_list:
                            logger.debug('%s: 300$e = %s', field_001, field_300['e'])
                    else:
                        field_300_3_no += 1
                        for field_001 in field_001_list:
                            logger.debug('%s: 300$3 = %s', field_001, field_300['3'])

            field_852_list = record.get_fields('852')
            for field_852 in field_852_list:
                if '3' in field_852:
                    field_852_3_no += 1
                    field_001_list = record.get_fields('001')
                    for field_001 in field_001_list:
                        logger.debug('%s: 852$3 = %s', field_001, field_852['3'])

            if '3' in field_952:
                field_952_3_no += 1
                field_001_list = record.get_fields('001')
                for field_001 in field_001_list:
                    logger.debug('%s: 952$3 = %s', field_001, field_952['3'])


field_052_2_no = 0
field_055_2_no = 0
field_082_a_no = 0
field_084_2_no = 0
field_086_2_no = 0
field_852_2_no = 0


def inspect_classification_data(record):
    global field_052_2_no
    global field_055_2_no
    global field_082_a_no
    global field_084_2_no
    global field_086_2_no
    global field_852_2_no

    field_052_list = record.get_fields('052')
    for field_052 in field_052_list:
        if '2' in field_052:
            field_052_2_no += 1
            field_001_list = record.get_fields('001')
            for field_001 in field_001_list:
                logger.debug('%s: 052$2 = %s', field_001, field_052['2'])

    field_055_list = record.get_fields('055')
    for field_055 in field_055_list:
        if '2' in field_055:
            field_055_2_no += 1
            field_001_list = record.get_fields('001')
            for field_001 in field_001_list:
                logger.debug('%s: 055$2 = %s', field_001, field_055['2'])

    field_082_list = record.get_fields('082')
    for field_082 in field_082_list:
        if 'a' in field_082:
            field_082_a_no += 1
            field_001_list = record.get_fields('001')
            for field_001 in field_001_list:
                logger.debug('%s: 082$a = %s', field_001, field_082['a'])

    field_084_list = record.get_fields('084')
    for field_084 in field_084_list:
        if '2' in field_084:
            field_084_2_no += 1
            field_001_list = record.get_fields('001')
            for field_001 in field_001_list:
                logger.debug('%s: 084$2 = %s', field_001, field_084['2'])

    field_086_list = record.get_fields('086')
    for field_086 in field_086_list:
        if '2' in field_086:
            field_086_2_no += 1
            field_001_list = record.get_fields('001')
            for field_001 in field_001_list:
                logger.debug('%s: 086$2 = %s', field_001, field_086['2'])

    field_852_list = record.get_fields('852')
    for field_852 in field_852_list:
        if '2' in field_852:
            field_852_2_no += 1
            field_001_list = record.get_fields('001')
            for field_001 in field_001_list:
                logger.debug('%s: 852$2 = %s', field_001, field_852['2'])


subfield_code_counter = 0


def inspect_subfield(record, field_code, subfield_code):
    global subfield_code_counter

    field_list = record.get_fields(field_code)
    for field in field_list:
        if subfield_code in field:
            subfield_code_counter += 1
            field_001_list = record.get_fields('001')
            for field_001 in field_001_list:
                logger.debug('%s: %s$%s = %s', field_001, field_code, subfield_code, field[subfield_code])


def check_bibliographic_data(input_path):
    logger.info('check bibliographic data sturcture ...')
    global file_record_no
    global file_error_no

    with open(input_path, 'rb') as input_file:
        reader = MARCReader(input_file, force_utf8=True)

        for record in reader:
            file_record_no += 1
            record.as_dict()

            inspect_subfield(record, '952', 'J')
            inspect_classification_data(record)
            inspect_materials_specified_data(record)
            inspect_order_numbers(record)

    logger.info('Bibliographic data structure check done!')


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info("Please provide as argument:")
        logger.info("1) Path to bibliograhic data (directory) exports from Aleph.")
        sys.exit()

    input_directory = sys.argv[1]

    for filename in os.listdir(input_directory):
        if filename.endswith('.mrc'):
            file_record_no = 0
            file_error_no = 0
            without_extension = os.path.splitext(filename)[0]
            logger.info("Processing file '%s' ...", filename)
            check_bibliographic_data(input_directory + '/' + filename)
            total_record_no += file_record_no
            total_error_no += file_error_no
            logger.info("Number of records in marc file: %s", file_record_no)
            logger.info("Number of record errors in marc file: %s", file_error_no)

            logger.info("Current occurrences of inspected subfield code: %s", subfield_code_counter)
            logger.info("Current number of 052$2 subfields: %s", field_052_2_no)
            logger.info("Current number of 055$2 subfields: %s", field_055_2_no)
            logger.info("Current number of 082$a subfields: %s", field_082_a_no)
            logger.info("Current number of 084$2 subfields: %s", field_084_2_no)
            logger.info("Current number of 086$2 subfields: %s", field_086_2_no)
            logger.info("Current number of 852$2 subfields: %s", field_852_2_no)

            logger.info("Current number of 300$e and 300$3 subfield combinations: %s", field_300_e_and_3_comb_no)
            logger.info("Current number of 300$e subfields: %s", field_300_e_no)
            logger.info("Current number of 300$3 subfields: %s", field_300_3_no)
            logger.info("Current number of 852$3 subfields: %s", field_852_3_no)
            logger.info("Current number of 952$3 subfields: %s", field_952_3_no)
            logger.info("Current number of 952$A subfields: %s", field_952_A_no)
            logger.info("Current number of 'R/2005-397 order number' subfields: %s", special_order_number_counter)

            logger.info("File '%s' processed.\n", filename)

    logger.info("Total occurrences of inspected subfield code: %s", subfield_code_counter)
    logger.info("Total number of 052$2 subfields: %s", field_052_2_no)
    logger.info("Total number of 055$2 subfields: %s", field_055_2_no)
    logger.info("Total number of 082$a subfields: %s", field_082_a_no)
    logger.info("Total number of 084$2 subfields: %s", field_084_2_no)
    logger.info("Total number of 086$2 subfields: %s", field_086_2_no)
    logger.info("Total number of 852$2 subfields: %s", field_852_2_no)

    logger.info("Total number of 300$e and 300$3 subfield combinations: %s", field_300_e_and_3_comb_no)
    logger.info("Total number of 300$e subfields: %s", field_300_e_no)
    logger.info("Total number of 300$3 subfields: %s", field_300_3_no)
    logger.info("Total number of 852$3 subfields: %s", field_852_3_no)
    logger.info("Total number of 952$3 subfields: %s", field_952_3_no)
    logger.info("Total number of 952$A subfields: %s", field_952_A_no)
    logger.info("Total number of 'R/2005-397 order number' subfields: %s", special_order_number_counter)

    logger.info("Total number of record errors: %s", total_error_no)
    logger.info("Total number of records: %s", total_record_no)
