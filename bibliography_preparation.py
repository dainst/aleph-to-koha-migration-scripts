from pymarc import MARCReader, MARCWriter

import logging
import os
import sys

import lib.database_connections.mariadb as mariadb
import lib.mappings.library_keys as library_keys
import lib.mappings.marc_mappings as marc_mappings
import lib.oracle_helper.dates as dates_helper

# This script currently serves the following purposes:
#   1) Mapping viable headings in the bibliographic data via String comparison (what Aleph also does internally)
#      to the authority data exported from Koha. In case of a match, Koha's internal authority ID gets
#      added to the bibliographic heading (subfield '9').
#   2) Library keys are mapped between Aleph and Koha. The keys got refactored in Koha, to add more naming consistency.

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler = logging.FileHandler('./bibliography_preparation.log')
# file_handler.setLevel(logging.INFO)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.ERROR)
# file_handler.setFormatter(formatter)
# console_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
# logger.addHandler(console_handler)

ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING = list()

holding_field_max = [None, 0]
holding_field_counter = 0
file_record_no = 0
total_record_no = 0
record_error_no = 0
file_error_no = 0
total_error_no = 0


def map_aleph_string_field(marc_field_code, marc_subfield_code, aleph_item_field_name, aleph_item_field_value):
    if aleph_item_field_value is None:
        logger.debug("Field No. %s: %s$%s = '%s', no valid '%s' found!", holding_field_counter,
                     marc_field_code, marc_subfield_code, aleph_item_field_value, aleph_item_field_name)
    else:
        logger.debug("Field No. %s: %$% = '%s', valid '%' code found.", holding_field_counter,
                     marc_field_code, marc_subfield_code, aleph_item_field_value, aleph_item_field_name)


def map_not_for_loan(subfield_952_J, subfield_952_1):
    not_for_loan = '1'

    if subfield_952_1 is not None or subfield_952_1 != 'Missing' or subfield_952_1 != 'Misshelved' or \
            subfield_952_1 != 'MI' or subfield_952_1 != 'MS':
        if subfield_952_1 == 'On order' or subfield_952_1 == 'OR':
            not_for_loan = '-1'
        elif subfield_952_1 == 'In Process' or subfield_952_1 == 'GG':
            not_for_loan == '-2'
        elif subfield_952_1 == 'Undeliverable' or subfield_952_1 == 'NL':
            not_for_loan == '-3'
        elif subfield_952_1 == 'Binding' or subfield_952_1 == 'BD':
            not_for_loan == '-4'
        elif subfield_952_1 == 'Cancelled' or subfield_952_1 == 'CA':
            not_for_loan == '-5'
        elif subfield_952_1 == 'Order initiat.' or subfield_952_1 == 'OI':
            not_for_loan == '-1'
        elif subfield_952_1 == 'Not Arrived' or subfield_952_1 == 'NA':
            not_for_loan == '-6'
        elif subfield_952_1 == 'Not published' or subfield_952_1 == 'NP':
            not_for_loan == '-7'
    elif subfield_952_J == '04':
        not_for_loan = '2'

    logger.debug("Field No. %s: 952$7 = '%s', valid 'Not for loan' found.", holding_field_counter, not_for_loan)

    return not_for_loan


def map_restrictions(subfield_952_c):
    restricted = '0'

    if subfield_952_c == 'RARA' or subfield_952_c == 'RARAH':
        restricted = '1'
    logger.debug("Field No. %s: 952$5 = '%s', valid 'Restrictions' found.", holding_field_counter, restricted)

    return restricted


def copy_materials_specified(field_300_list):
    materials_specified = None

    for field_300 in field_300_list:
        if 'e' in field_300 or '3' in field_300:
            if 'e' in field_300 and '3' in field_300:
                subfield_300_e = field_300['e']
                subfield_300_3 = field_300['3']
                if not 1 > len(subfield_300_e + ', ' + subfield_300_3) > 65535:
                    materials_specified = subfield_300_e + ', ' + subfield_300_3
                    logger.debug("Field No. %s: 952$3 = '%s', valid 'Materials specified' copied from 300$e and 300$3.",
                                 holding_field_counter, materials_specified)
                else:
                    logger.debug("Field No. %s: 952$3 = '%s', "
                                 "no valid 'Materials specified' available from 300$e combined with 300$3!",
                                 holding_field_counter, materials_specified)
            elif 'e' in field_300:
                subfield_300_e = field_300['e']
                if 1 > len(subfield_300_e) > 65535:
                    materials_specified = subfield_300_e
                    logger.debug("Field No. %s: 952$3 = '%s', valid 'Materials specified' copied from 300$e.",
                                 holding_field_counter, materials_specified)
                else:
                    logger.debug("Field No. %s: 952$3 = '%s', no valid 'Materials specified' available from 300$e!",
                                 holding_field_counter, materials_specified)
            else:
                subfield_300_3 = field_300['3']
                if 1 > len(subfield_300_3) > 65535:
                    materials_specified = subfield_300_3
                    logger.debug("Field No. %s: 952$3 = '%s', valid 'Materials specified' copied from 300$3.",
                                 holding_field_counter, materials_specified)
                else:
                    logger.debug("Field No. %s: 952$3 = '%s', no valid 'Materials specified' available from 300$3!",
                                 holding_field_counter, materials_specified)
        else:
            logger.debug("Field No. %s: 952$3 = '%s', no valid 'Materials specified' in 300$e and 300$3 found!",
                         holding_field_counter, materials_specified)

    return materials_specified


def map_materials_specified(subfield_952_3):
    if 1 > len(subfield_952_3) > 65535:
        logger.debug("Field No. %s: 952$3 = '%s', no valid 'Materials specified' found!",
                     holding_field_counter, subfield_952_3)

        return None
    else:
        logger.debug("Field No. %s: 952$3 = '%s', valid 'Materials specified' found.",
                     holding_field_counter, subfield_952_3)

        return subfield_952_3


def map_classification_source():
    classification_source = 'z'
    logger.debug("Field No. %s: 952$2 = '%s', valid 'Classification source' found.",
                 holding_field_counter, classification_source)

    return classification_source


def map_lost_status(subfield_952_1):
    lost_status = '0'

    if subfield_952_1 == 'MI' or subfield_952_1 == 'MS' or \
            subfield_952_1 == 'Missing' or subfield_952_1 == 'Misshelved':
        lost_status = '1'
    logger.debug("Field No. %s: 952$1 = '%s', valid 'Lost status' found.", holding_field_counter, lost_status)

    return lost_status


def map_public_note(subfield_952_z):
    if 1 > len(subfield_952_z) > 16777215:
        logger.debug("Field No. %s: 952$z = '%s', no valid 'Public note' found!",
                     holding_field_counter, subfield_952_z)

        return None
    else:
        logger.debug("Field No. %s: 952$z = '%s', valid 'Public note' found.",
                     holding_field_counter, subfield_952_z)

        return subfield_952_z


def map_item_type(subfield_952_y):
    item_type = None

    if subfield_952_y is None:
        logger.error("Field No. %s: No required subfield 'y' found!", holding_field_counter)
    else:
        item_type = marc_mappings.map_material(subfield_952_y)

        if item_type is None:
            logger.error("Field No. %s: 952$y = '%s', no valid 'Item type' code found!",
                         holding_field_counter, subfield_952_y)
        else:
            logger.debug("Field No. %s: 952$y = '%s', valid 'Item type' code found.",
                         holding_field_counter, item_type)

    return item_type


def map_nonpublic_note(subfield_952_x):
    if 1 > len(subfield_952_x) > 16777215:
        logger.debug("Field No. %s: 952$x = '%s', no valid 'Nonpublic note' found!",
                     holding_field_counter, subfield_952_x)

        return None
    else:
        logger.debug("Field No. %s: 952$x = '%s', valid 'Nonpublic note' found.",
                     holding_field_counter, subfield_952_x)

        return subfield_952_x


def map_copy_number(subfield_952_t):
    if 1 > len(subfield_952_t) > 32:
        # logger.error("Aleph 'copy number' length exceeds Koha 'copy number' length!\n")
        logger.debug("Field No. %s: 952$t = '%s', no valid 'Copy number' found!",
                     holding_field_counter, subfield_952_t)

        return None
    else:
        logger.debug("Field No. %s: 952$t = '%s', valid 'Copy number' found.",
                     holding_field_counter, subfield_952_t)

        return subfield_952_t


def map_barcode(subfield_952_p):
    if 1 > len(subfield_952_p) > 20:
        logger.error("Aleph 'barcode' length exceeds Koha 'Barcode' length!\n")
        logger.warning("Field No. %s: 952$p = '%s', no valid 'Barcode' found!",
                       holding_field_counter, subfield_952_p)

        return None
    else:
        logger.debug("Field No. %s: 952$p = '%s', valid 'Barcode' found.",
                     holding_field_counter, subfield_952_p)

        return subfield_952_p


def map_call_number(subfield_952_o):
    if 1 > len(subfield_952_o) > 255:
        # logger.error("Length of 'call number' not in between 1 and 255!\n")
        logger.debug("Field No. %s: 952$o = '%s', no valid 'Call number' found!",
                     holding_field_counter, subfield_952_o)

        return None
    else:
        logger.debug("Field No. %s: 952$o = '%s', valid 'Call number' found.",
                     holding_field_counter, subfield_952_o)

        return subfield_952_o


def map_inventory_number(subfield_952_i):
    if 1 > len(subfield_952_i) > 32:
        # logger.error("Aleph 'inventory number' length exceeds Koha 'stock number' length!\n")
        logger.debug("Field No. %s: 952$i = '%s', no valid 'Inventory number' found!",
                     holding_field_counter, subfield_952_i)

        return None
    else:
        logger.debug("Field No. %s: 952$i = '%s', valid 'Inventory number' found.",
                     holding_field_counter, subfield_952_i)

        return subfield_952_i


def rstrip_purchase_price(purchase_price):
    length = len(purchase_price)
    rindex = length - 1
    if length > 0:
        if not purchase_price[-1].isdigit():
            while rindex >= 0:
                if purchase_price[rindex].isdigit():
                    break
                rindex -= 1

            if rindex == 0:
                purchase_price = '0.00'
            else:
                purchase_price = purchase_price[0:rindex + 1]

    return purchase_price


def lstrip_purchase_price(purchase_price):
    lindex = 0
    if not purchase_price[0].isdigit():
        for char in purchase_price:
            if char.isdigit():
                break
            lindex += 1

        if lindex == len(purchase_price):
            purchase_price = '0.00'
        else:
            purchase_price = purchase_price[lindex:]

    return purchase_price


def format_purchase_price(aleph_purchase_price):
    purchase_price = aleph_purchase_price.strip().replace(',', '.')

    if not (purchase_price[0].isdigit() and purchase_price[-1].isdigit()):
        purchase_price = lstrip_purchase_price(purchase_price)
        purchase_price = rstrip_purchase_price(purchase_price)
        purchase_price = '{0:.2f}'.format(float(purchase_price))

    if 1 > len(purchase_price) > 11:
        # logger.error('Koha purchase price length: %s', len(koha_purchase_price))
        # logger.error("Koha purchase price: %s", koha_purchase_price)

        return None
    else:

        return purchase_price


def map_purchase_price(subfield_952_g):
    purchase_price = format_purchase_price(subfield_952_g)

    if purchase_price is None:
        pass
        logger.debug("Field No. %s: 952$g = '%s', no valid 'Purchase price' found!",
                     holding_field_counter, subfield_952_g)
    else:
        pass
        logger.debug("Field No. %s: 952$g = '%s', valid 'Purchase price' found.",
                     holding_field_counter, purchase_price)

    return purchase_price


def map_aleph_vendor_code(aleph_z70_vendor_code):
    global ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING

    for (aleph_code, koha_id) in ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING:
        # logger.info("aleph_code: %s", aleph_code)
        # logger.info("koha_id: %s", koha_id)
        if aleph_z70_vendor_code == aleph_code:

            return koha_id
    else:

        return None


def map_source_of_acquisition(subfield_952_e):
    source_of_acquisition = map_aleph_vendor_code(subfield_952_e)

    if source_of_acquisition is None:
        pass
        logger.debug("Field No. %s: 952$e = '%s', no valid 'Source of aquisition' found!",
                     holding_field_counter, subfield_952_e)
    else:
        pass
        logger.debug("Field No. %s: 952$e = '%s', valid 'Source of aquisition' found.",
                     holding_field_counter, source_of_acquisition)

    return source_of_acquisition


def map_aleph_date_field(marc_field_code, marc_subfield_code, field_name, field_value):
    date = dates_helper.process_aleph_date(field_value)

    if date is None:
        logger.debug("Field No. %s: %s$%s = '%s', no valid '%s' found!",
                     holding_field_counter, marc_field_code, marc_subfield_code, field_value, field_name)
    else:
        logger.debug("Field No. %s: %s$%s = '%s', valid '%s' found.",
                     holding_field_counter, marc_field_code, marc_subfield_code, date, field_name)

    return date


def map_shelving_location_code(subfield_952_c, koha_library_code):
    shelving_location_code = marc_mappings.map_shelving_location(subfield_952_c, koha_library_code)

    if shelving_location_code is None:
        logger.debug("Field No. %s: 952$c = '%s', no valid 'Shelving location' found!",
                     holding_field_counter, subfield_952_c)
    else:
        logger.debug("Field No. %s: 952$c = '%s', valid 'Shelving location' found.",
                     holding_field_counter, shelving_location_code)

    return shelving_location_code


def map_holding_library(subfield_952_b):
    holding_library = None

    if subfield_952_b is None:
        logger.error("Field No. %s: No required subfield 'b' found!", holding_field_counter)
    else:
        holding_library = library_keys.map_aleph_key(subfield_952_b)
        if holding_library is None:
            logger.error("Field No. %s: 952$b = '%s', no valid 'Holding library' code found!",
                         holding_field_counter, subfield_952_b)
        else:
            logger.debug("Field No. %s: 952$b = '%s', valid 'Holding library' code found.",
                         holding_field_counter, holding_library)

    return holding_library


def map_owning_library(subfield_952_a):
    owning_library = None

    if subfield_952_a is None:
        logger.error("Field No. %s: No required subfield 'a' found!", holding_field_counter)
    else:
        owning_library = library_keys.map_aleph_key(subfield_952_a)
        if owning_library is None:
            logger.error("Field No. %s: 952$a = '%s' , no valid 'Owning library' code found!",
                         holding_field_counter, subfield_952_a)
        else:
            logger.debug("Field No. %s: 952$a = '%s', valid 'Owning library' code found.",
                         holding_field_counter, owning_library)

    return owning_library


def check_required_subfields(field_952):
    is_success = False

    if all(subfields in field_952 for subfields in ('a', 'b', 'y')):
        logger.debug("Field No. %s: All required subfieds 'a', 'b', and 'y' found.", holding_field_counter)
        is_success = True
    elif 'y' in field_952 and ('a' or 'b' in field_952):
        if 'a' not in field_952:
            field_952.add_subfield('a', field_952['b'])
            logger.debug(
                "Field No. %s: Required subfield 'a' not found! Copy subfield 'b' into subfield 'a': 952$a = %s",
                holding_field_counter, field_952['a']
            )
        if 'b' not in field_952:
            field_952.add_subfield('b', field_952['a'])
            logger.debug(
                "Field No. %s: Required subfield 'b' not found! Copy subfield 'a' into subfield 'b': 952$b = %s",
                holding_field_counter, field_952['b']
            )
        is_success = True
    else:
        logger.error('Field No. %s: Neither required subfields 952$a and 952$b found nor required subfield 952$y!',
                     holding_field_counter)

    return is_success


def prepare_holding_data(record):
    global holding_field_max
    global holding_field_counter
    global file_error_no
    global record_error_no
    global file_record_no

    logger.info("Processing holding information of Marc record: '%s' ...", record.leader)

    is_record_format_error = False
    is_record_format_warning = False
    is_record_format_info = False
    is_record_format_debugging = False

    holding_field_code = '952'
    marc_holding_fields = record.get_fields(holding_field_code)
    holding_field_no = len(marc_holding_fields)
    if holding_field_no > holding_field_max[1]:
        holding_field_max[0] = record.leader
        holding_field_max[1] = holding_field_no

    logger.info("%s holding field(s) found.", holding_field_no)

    holding_field_counter = 1
    record_error_no = 0
    for field_952 in marc_holding_fields:
        logger.debug("Field No. %s: %s", holding_field_counter, field_952)

        if check_required_subfields(field_952):

            # '952$a' Owning Library (required by Koha)
            koha_owning_library = map_owning_library(field_952['a'])
            if koha_owning_library is None:
                logger.error('Field No. %s: Skipping field: %s', holding_field_counter, field_952)
                record.remove_field(field_952)
                is_record_format_error = True
                record_error_no += 1
                holding_field_counter += 1
                continue
            else:
                field_952['a'] = koha_owning_library

            # '952$b' Holding library (required by Koha)
            koha_holding_library = map_holding_library(field_952['b'])
            if koha_holding_library is None:
                logger.error('Field No. %s: Skipping field: %s', holding_field_counter, field_952)
                record.remove_field(field_952)
                is_record_format_error = True
                record_error_no += 1
                holding_field_counter += 1
                continue
            else:
                field_952['b'] = koha_holding_library

            # '952$c' Shelving location code
            subfield_952_c = field_952['c']
            if subfield_952_c is not None:
                koha_shelving_location = map_shelving_location_code(subfield_952_c, koha_owning_library)
                if koha_shelving_location is None:
                    logger.info("Field No. %s: Skipping subfield 'c' = %s", holding_field_counter, subfield_952_c)
                    field_952.delete_subfield('c')
                else:
                    field_952['c'] = koha_shelving_location

            # '952$d' Date acquired
            date_acquired_subfield_code = 'd'
            subfield_952_d = field_952[date_acquired_subfield_code]
            if subfield_952_d is not None:
                koha_date_acquired = map_aleph_date_field(holding_field_code, date_acquired_subfield_code,
                                                          'Date aquired', subfield_952_d)
                if koha_date_acquired is None:
                    logger.info("Field No. %s: Skipping subfield '%s' = %s",
                                holding_field_counter, date_acquired_subfield_code, subfield_952_d)
                    field_952.delete_subfield(date_acquired_subfield_code)
                else:
                    field_952[date_acquired_subfield_code] = koha_date_acquired

            # '952$e' Source of acquisition
            subfield_952_e = field_952['e']
            if subfield_952_e is not None:
                koha_source_of_aquisition = map_source_of_acquisition(subfield_952_e)
                if koha_source_of_aquisition is None:
                    logger.info("Field No. %s: Skipping subfield 'e' = %s", holding_field_counter, subfield_952_e)
                    field_952.delete_subfield('e')
                else:
                    field_952['e'] = koha_source_of_aquisition

            # '952$f' Coded location qualifier
            # 'This has no function in Koha.'
            subfield_952_f = field_952['f']
            if subfield_952_f is not None:
                logger.info("Field No. %s: Skipping subfield 'f' = %s", holding_field_counter, subfield_952_f)
                field_952.delete_subfield('f')

            # '952$g' Purchase price
            subfield_952_g = field_952['g']
            if subfield_952_g is not None:
                koha_purchase_prise = map_purchase_price(subfield_952_g)
                if koha_purchase_prise is None:
                    logger.info("Field No. %s: Skipping subfield 'g' = %s", holding_field_counter, subfield_952_g)
                    field_952.delete_subfield('g')
                else:
                    field_952['g'] = koha_purchase_prise

            # TODO '952$h' Serial enumeration
            subfield_952_h = field_952['h']
            if subfield_952_h is not None:
                pass

            # '952$i' Inventory number
            subfield_952_i = field_952['i']
            if subfield_952_i is not None:
                koha_inventory_number = map_inventory_number(subfield_952_i)
                if koha_inventory_number is None:
                    logger.info("Field No. %s: Skipping subfield 'i' = %s", holding_field_counter, subfield_952_i)
                    field_952.delete_subfield('i')
                else:
                    field_952['i'] = koha_inventory_number

            # '952$j' Shelving control number -> currently not applicable for Aleph
            subfield_952_j = field_952['j']
            if subfield_952_j is not None:
                logger.info("Field No. %s: Skipping subfield 'j' = %s", holding_field_counter, subfield_952_j)
                field_952.delete_subfield('j')

            # '952$k' Unused in Koha.
            subfield_952_k = field_952['k']
            if subfield_952_k is not None:
                logger.info("Field No. %s: Skipping subfield 'k' = %s", holding_field_counter, subfield_952_k)
                field_952.delete_subfield('k')

            # '952$l' Total Checkouts -> currently not applicable for Aleph
            subfield_952_l = field_952['l']
            if subfield_952_l is not None:
                logger.info("Field No. %s: Skipping subfield 'l' = %s", holding_field_counter, subfield_952_l)
                field_952.delete_subfield('l')

            # '952$m' Total Renewals -> currently not applicable for Aleph
            subfield_952_m = field_952['m']
            if subfield_952_m is not None:
                logger.info("Field No. %s: Skipping subfield 'm' = %s", holding_field_counter, subfield_952_m)
                field_952.delete_subfield('m')

            # '952$n' Total Holds -> currently not applicable for Aleph
            subfield_952_n = field_952['n']
            if subfield_952_n is not None:
                logger.info("Field No. %s: Skipping subfield 'n' = %s", holding_field_counter, subfield_952_n)
                field_952.delete_subfield('n')

            # '952$o' Koha full call number
            subfield_952_o = field_952['o']
            if subfield_952_o is not None:
                koha_call_number = map_call_number(subfield_952_o)
                if koha_call_number is None:
                    logger.info("Field No. %s: Skipping subfield 'o' = %s", holding_field_counter, subfield_952_o)
                    field_952.delete_subfield('o')
                else:
                    field_952['o'] = koha_call_number

            # '952$p' Barcode (required for circulation)
            subfield_952_p = field_952['p']
            if subfield_952_p is None:
                logger.warning("Field No. %s: No required subfield 'p' found!", holding_field_counter)
            else:
                koha_barcode = map_barcode(subfield_952_p)
                if koha_barcode is None:
                    logger.warning("Field No. %s: Skipping subfield 'p' in marc field %s",
                                   holding_field_counter, field_952)
                    field_952.delete_subfield('p')
                    is_record_format_error = True
                    record_error_no += 1
                else:
                    field_952['p'] = koha_barcode

            # '952$q' Due date -> currently not applicable for Aleph
            subfield_952_q = field_952['q']
            if subfield_952_q is not None:
                logger.info("Field No. %s: Skipping subfield 'q' = %s", holding_field_counter, subfield_952_q)
                field_952.delete_subfield('q')

            # '952$r' Date last seen -> currently not applicable for Aleph
            subfield_952_r = field_952['r']
            if subfield_952_r is not None:
                logger.info("Field No. %s: Skipping subfield 'r' = %s", holding_field_counter, subfield_952_r)
                field_952.delete_subfield('r')

            # '952$s' Date last checked out -> currently not applicable for Aleph
            subfield_952_s = field_952['s']
            if subfield_952_s is not None:
                logger.info("Field No. %s: Skipping subfield 's' = %s", holding_field_counter, subfield_952_s)
                field_952.delete_subfield('s')

            # '952$t' Copy number
            subfield_952_t = field_952['t']
            if subfield_952_t is not None:
                koha_copy_number = map_copy_number(subfield_952_t)
                if koha_copy_number is None:
                    logger.info("Field No. %s: Skipping subfield 't' = %s", holding_field_counter, subfield_952_t)
                    field_952.delete_subfield('t')
                else:
                    field_952['t'] = koha_copy_number

            # '952$u' Uniform Resource Identifier -> currently not applicable for Aleph
            subfield_952_u = field_952['u']
            if subfield_952_u is not None:
                logger.info("Field No. %s: Skipping subfield 'u' = %s", holding_field_counter, subfield_952_u)
                field_952.delete_subfield('u')

            # '952$v' Replacement price -> currently not applicable for Aleph
            subfield_952_v = field_952['v']
            if subfield_952_v is not None:
                logger.info("Field No. %s: Skipping subfield 'v' = %s", holding_field_counter, subfield_952_v)
                field_952.delete_subfield('v')

            # '952$w' Price effective from -> currently not applicable for Aleph
            subfield_952_w = field_952['w']
            if subfield_952_w is not None:
                logger.info("Field No. %s: Skipping subfield 'w' = %s", holding_field_counter, subfield_952_w)
                field_952.delete_subfield('w')

            # '952$x' Nonpublic note
            subfield_952_x = field_952['x']
            if subfield_952_x is not None:
                koha_nonpublic_note = map_nonpublic_note(subfield_952_x)
                if koha_nonpublic_note is None:
                    logger.info("Field No. %s: Skipping subfield 'x' = %s", holding_field_counter, subfield_952_x)
                    field_952.delete_subfield('x')
                else:
                    field_952['x'] = koha_nonpublic_note

            # '952$y' Item type (required by Koha)
            koha_item_type = map_item_type(field_952['y'])
            if koha_item_type is None:
                logger.error('Field No. %s: Skipping field: %s', holding_field_counter, field_952)
                record.remove_field(field_952)
                is_record_format_error = True
                record_error_no += 1
                holding_field_counter += 1
                continue
            else:
                field_952['y'] = koha_item_type

            # '952$z' Public note
            subfield_952_z = field_952['z']
            if subfield_952_z is not None:
                koha_public_note = map_public_note(subfield_952_z)
                if koha_public_note is None:
                    logger.info("Field No. %s: Skipping subfield 'z' = %s", holding_field_counter, subfield_952_z)
                    field_952.delete_subfield('z')
                else:
                    field_952['z'] = koha_public_note

            # '952$0' Withdrawn status -> not applicable for Aleph
            subfield_952_0 = field_952['0']
            if subfield_952_0 is not None:
                logger.info("Field No. %s: Skipping subfield '0' = %s", holding_field_counter, subfield_952_0)
                field_952.delete_subfield('0')

            # '952$1' Lost status
            subfield_952_1 = field_952['1']
            if subfield_952_1 is not None:
                field_952['1'] = map_lost_status(subfield_952_1)

            # '952$2' Classification source
            subfield_952_2 = field_952['2']
            koha_classification_source = map_classification_source()
            if subfield_952_2 is not None:
                field_952['2'] = koha_classification_source
            else:
                field_952.add_subfield('2', koha_classification_source)
                logger.info("Field No. %s: Added subfield '2' = %s", holding_field_counter, koha_classification_source)

            # '952$3' Materials specified
            subfield_952_3 = field_952['3']
            if subfield_952_3 is not None:
                koha_materials_specified = map_materials_specified(subfield_952_3)
                if koha_materials_specified is None:
                    logger.info("Field No. %s: Skipping subfield '3' = %s", holding_field_counter, subfield_952_3)
                    field_952.delete_subfield('3')
                else:
                    field_952['3'] = koha_materials_specified
            elif koha_item_type == 'MX':
                field_300_list = record.get_fields('300')
                koha_materials_specified = copy_materials_specified(field_300_list)
                if koha_materials_specified is not None:
                    field_952.add_subfield('3', koha_materials_specified)
                    logger.info("Field No. %s: Added subfield '3' = %s",
                                holding_field_counter, koha_materials_specified)

            # '952$4' Damaged status -> not applicable for Aleph
            subfield_952_4 = field_952['4']
            if subfield_952_4 is not None:
                logger.info("Field No. %s: Skipping subfield '4' = %s", holding_field_counter, subfield_952_4)
                field_952.delete_subfield('4')

            # '952$5' Use restrictions
            subfield_952_5 = field_952['5']
            if subfield_952_c is not None:
                koha_restrictions = map_restrictions(subfield_952_c)
                if subfield_952_5 is not None:
                    field_952['5'] = koha_restrictions
                else:
                    field_952.add_subfield('5', koha_restrictions)
                    logger.info("Field No. %s: Added subfield '5' = %s", holding_field_counter, koha_restrictions)

            # '952$6' Koha normalized classification for sorting -> not applicable for Aleph
            subfield_952_6 = field_952['6']
            if subfield_952_6 is not None:
                logger.info("Field No. %s: Skipping subfield '6' = %s", holding_field_counter, subfield_952_6)
                field_952.delete_subfield('6')

            # '952$7' Not for loan
            subfield_952_7 = field_952['7']
            subfield_952_J = field_952['J']
            koha_not_for_loan = map_not_for_loan(subfield_952_J, subfield_952_1)
            if subfield_952_7 is not None:
                field_952['7'] = koha_not_for_loan
            else:
                field_952.add_subfield('7', koha_not_for_loan)
                logger.info("Field No. %s: Added subfield '7' = %s", holding_field_counter, koha_not_for_loan)

            # '952$8' Collection code -> not applicable for Aleph
            subfield_952_8 = field_952['8']
            if subfield_952_8 is not None:
                logger.info("Field No. %s: Skipping subfield '8' = %s", holding_field_counter, subfield_952_8)
                field_952.delete_subfield('8')

            # '952$9' Item number (autogenerated) -> not applicable for Aleph
            subfield_952_9 = field_952['9']
            if subfield_952_9 is not None:
                logger.info("Field No. %s: Skipping subfield '9' = %s", holding_field_counter, subfield_952_9)
                field_952.delete_subfield('9')

            # '952$A' Bestellnummer aus der Erwerbung
            order_number_subfield_code = 'A'
            subfield_952_A = field_952[order_number_subfield_code]
            map_aleph_string_field(holding_field_code, order_number_subfield_code, 'Z30_ORDER_NUMBER', subfield_952_A)

            # '952$C' Umlauf-Notiz
            note_circulation_subfield_code = 'C'
            subfield_952_C = field_952[note_circulation_subfield_code]
            map_aleph_string_field(holding_field_code, note_circulation_subfield_code,
                                 'Z30_NOTE_CIRCULATION', subfield_952_C)

            # '952$D' Beschreibung
            description_subfield_code = 'D'
            subfield_952_D = field_952[description_subfield_code]
            map_aleph_string_field(holding_field_code, description_subfield_code, 'Z30_DESCRIPTION', subfield_952_D)

            # '952$E' Erwartet zum (Zeitschriftenheft) Datum
            expected_arrival_date_subfield_code = 'E'
            subfield_952_E = field_952[expected_arrival_date_subfield_code]
            if subfield_952_E is not None:
                expected_arrival_date = map_aleph_date_field(holding_field_code, expected_arrival_date_subfield_code,
                                                          'Z30_EXPECTED_ARRIVAL_DATE', subfield_952_E)
                if expected_arrival_date is None:
                    logger.info("Field No. %s: Skipping subfield '%s' = %s",
                                holding_field_counter, expected_arrival_date_subfield_code, subfield_952_E)
                    field_952.delete_subfield(expected_arrival_date_subfield_code)
                else:
                    field_952[expected_arrival_date_subfield_code] = expected_arrival_date

            # TODO '952$H' Jahreszählung bei Zetischriftenheften

            # '952$J' Exemplarstatus
            item_status_subfield_code = 'J'
            subfield_952_J = field_952[item_status_subfield_code]
            map_aleph_string_field(holding_field_code, item_status_subfield_code, 'Z30_ITEM_STATUS', subfield_952_J)

            # '952$O' 2. Signatur
            call_no_2_subfield_code = 'O'
            subfield_952_O = field_952[call_no_2_subfield_code]
            map_aleph_string_field(holding_field_code, call_no_2_subfield_code, 'Z30_CALL_NO_2', subfield_952_O)

            # '952$P' Erfassungsdatum
            open_date_subfield_code = 'P'
            subfield_952_P = field_952[open_date_subfield_code]
            if subfield_952_P is not None:
                open_date = map_aleph_date_field(holding_field_code, open_date_subfield_code,
                                                 'Z30_OPEN_DATE', subfield_952_P)
                if open_date is None:
                    logger.info("Field No. %s: Skipping subfield '%s' = %s",
                                holding_field_counter, open_date_subfield_code, subfield_952_P)
                    field_952.delete_subfield(open_date_subfield_code)
                else:
                    field_952[open_date_subfield_code] = open_date

            # '952$S' Ex-Geschäftsgang-Status
            # '952$T' Statistikwerte
            item_process_status_subfield_code = 'S'
            subfield_952_S = field_952[item_process_status_subfield_code]
            map_aleph_string_field(holding_field_code, item_process_status_subfield_code,
                                   'Z30_ITEM_PROCESS_STATUS ', subfield_952_S)

            # '952$U' Änderungsdatum
            update_date_subfield_code = 'U'
            subfield_952_U = field_952[update_date_subfield_code]
            if subfield_952_U is not None:
                update_date = map_aleph_date_field(holding_field_code, update_date_subfield_code,
                                                   'Z30_OPEN_DATE', subfield_952_U)
                if update_date is None:
                    logger.info("Field No. %s: Skipping subfield '%s' = %s",
                                holding_field_counter, update_date_subfield_code, subfield_952_U)
                    field_952.delete_subfield(update_date_subfield_code)
                else:
                    field_952[update_date_subfield_code] = update_date
        else:
            logger.error('Field No. %s: Skipping field: %s', holding_field_counter, field_952)
            record.remove_field(field_952)
            is_record_format_error = True
            record_error_no += 1

        logger.debug("Field No. %s: %s", holding_field_counter, field_952)
        holding_field_counter += 1

    file_record_no += 1

    if is_record_format_error:
        logger.error('In Record:\n%s', record)
    elif is_record_format_warning:
        logger.warning('In Record:\n%s', record)
    elif is_record_format_info:
        logger.info('In Record:\n%s', record)
    elif is_record_format_debugging:
        logger.debug('In Record:\n%s', record)

    logger.info('%s record error(s) found.', record_error_no)
    logger.info("Marc Record '%s' process completed!\n", record.leader)

    return record


def link_bibliographic_headings_to_koha_authority_ids(bibliographic_record, heading_to_authority_id_mapping):
    for field in marc_mappings.AUTHORITY_FIELDS_TO_BIBLIOGRAPHIC_FIELDS_MAPPING:
        for bibliographic_record_field in bibliographic_record.get_fields(field[1]):
            koha_id = heading_to_authority_id_mapping.get(bibliographic_record_field.as_marc('utf8'))

            if koha_id is not None:
                bibliographic_record_field.add_subfield('9', koha_id)

    return bibliographic_record


def get_aleph_vendor_code_koha_bookseller_name_mapping():
    mariadb.open_mariadb_connection()
    result = mariadb.get_aleph_vendor_code_koha_aqbookseller_mapping()
    logger.debug('get_aleph_vendor_code_koha_aqbookseller_mapping - Result:\n%s', result)
    mariadb.close_mariadb_connection()

    return result


def process_bibliographic_data(input_path, output_path, mapping):
    global file_error_no

    with open(input_path, 'rb') as input_file:
        with open(output_path, 'wb') as output_file:
            reader = MARCReader(input_file, force_utf8=True)
            writer = MARCWriter(output_file)

            for record in reader:
                record = link_bibliographic_headings_to_koha_authority_ids(record, mapping)
                record = prepare_holding_data(record)
                # TODO: instead of deleting 999, move to different fields/subfields
                record.remove_fields('999')
                file_error_no += record_error_no
                writer.write(record)

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
                special_order_number_counter +=1

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

            # inspect_subfield(record, '952', 'O')
            # inspect_classification_data(record)
            # inspect_materials_specified_data(record)
            # inspect_order_numbers(record)

    logger.info('Bibliographic data structure check done!')


def create_authority_heading_to_authority_id_mapping(file_path):
    logger.info('Creating authority-heading-to-authority-id mapping based on exported authority data...')

    result = {}
    with open(file_path, 'rb') as authority_file:
        reader = MARCReader(authority_file, force_utf8=True)
        for authority_record in reader:
            for field in marc_mappings.AUTHORITY_FIELDS_TO_BIBLIOGRAPHIC_FIELDS_MAPPING:
                auth_field = field[0]
                if authority_record[auth_field] is not None:
                    heading = authority_record[auth_field].as_marc('utf-8')
                    result[heading] = authority_record['001'].data

    logger.info('Done.\n')

    return result


if __name__ == '__main__':

    if len(sys.argv) != 4:
        logger.info("Please provide as argument:")
        logger.info("1) Path to bibliograhic data (directory) exports from Aleph.")
        logger.info("2) Path to authority data (file) export from Koha.")
        logger.info("3) Path to output directory for results.")
        sys.exit()

    authority_heading_to_authority_id_mapping = create_authority_heading_to_authority_id_mapping(sys.argv[2])
    input_directory = sys.argv[1]
    output_directory = sys.argv[3]

    if not os.path.dirname(output_directory).endswith('/'):
        output_directory += '/'

    if not os.path.exists(os.path.dirname(output_directory)) and os.path.dirname(output_directory) != '':
        os.makedirs(os.path.dirname(output_directory))

    ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING = get_aleph_vendor_code_koha_bookseller_name_mapping()
    if len(ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING) < 1:
        exit("'AQBOOKSELLERS' table is empty!")

    for filename in os.listdir(input_directory):
        if filename.endswith('.mrc'):
            file_record_no = 0
            file_error_no = 0
            without_extension = os.path.splitext(filename)[0]
            logger.info("Processing file '%s' ...", filename)
            check_bibliographic_data(input_directory + '/' + filename)
            process_bibliographic_data(
                input_directory + '/' + filename,
                output_directory + without_extension + '-preprocessed.mrc',
                authority_heading_to_authority_id_mapping
            )
            total_record_no += file_record_no
            total_error_no += file_error_no
            logger.info("Number of records in marc file: %s", file_record_no)
            logger.info("Number of record errors in marc file: %s", file_error_no)

            """logger.info("Current occurrences of inspected subfield code: %s", subfield_code_counter)
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
            logger.info("Current number of 'R/2005-397 order number' subfields: %s", special_order_number_counter)"""

            logger.info("File '%s' processed.\n", filename)

    """logger.info("Total occurrences of inspected subfield code: %s", subfield_code_counter)
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
    logger.info("Total number of 'R/2005-397 order number' subfields: %s", special_order_number_counter)"""

    logger.info("Holding field number maximum: %s (%s)", holding_field_max[1], holding_field_max[0])
    logger.info("Total number of record errors: %s", total_error_no)
    logger.info("Total number of records: %s", total_record_no)
