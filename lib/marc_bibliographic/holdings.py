import logging

import lib.database_connections.oracle as oracle
import lib.mappings.library_keys as library_keys
import lib.mappings.marc_mappings as marc_mappings
import lib.oracle_helper.dates as dates_helper

HOLDING_FIELD_CODE = '952'
ALEPH_ITEM_PRICE_LIST = dict()
ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING = dict()
BARCODE_TO_ZENON_ID_MAPPING = dict()

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

thesaurus_field_counter = 0
holding_field_max = [None, 0]


def map_aleph_item_statistic(aleph_item_statistic, aleph_item_order_number):
    item_statistic = None

    if aleph_item_statistic == '04':
        item_statistic = 'Tausch'
    elif aleph_item_statistic == '05':
        item_statistic = 'Erwerbungsart unbekannt'
    elif aleph_item_statistic == '01' or (aleph_item_statistic == '  / / /001' and aleph_item_order_number is not None):
        item_statistic = 'Kauf'
    elif aleph_item_statistic == '02':
        item_statistic = 'Geschenk'
    elif aleph_item_statistic == '14':
        item_statistic = 'Vor- und Nachlass'
    elif aleph_item_statistic == '15':
        item_statistic = 'Kauf-Fortsetzung'
    elif aleph_item_statistic == '03':
        item_statistic = 'Pflichtexemplar'
    elif aleph_item_statistic == '16':
        item_statistic = 'Mitgliedschaft'
    elif aleph_item_statistic == '06' or aleph_item_statistic == '08' or aleph_item_statistic == '07':
        item_statistic = 'Fortlaufende Werke'
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$T = '%s', no valid 'Z30_ITEM_STATISTIC' code found!",
                         thesaurus_field_counter, aleph_item_statistic)

    if item_statistic is not None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$T = '%s', valid 'Z30_ITEM_STATISTIC' found.",
                         thesaurus_field_counter, item_statistic)

    return item_statistic


def map_aleph_string_field(marc_field_code, marc_subfield_code, aleph_item_field_name, aleph_item_field_value):
    if aleph_item_field_value is None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: %s$%s = '%s', no valid '%s' found!", thesaurus_field_counter,
                         marc_field_code, marc_subfield_code, aleph_item_field_value, aleph_item_field_name)
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: %s$%s = '%s', valid '%s' code found.", thesaurus_field_counter,
                         marc_field_code, marc_subfield_code, aleph_item_field_value, aleph_item_field_name)


def map_not_for_loan(aleph_item_status, aleph_item_process_status):
    not_for_loan = '1'

    if aleph_item_process_status is not None or \
            aleph_item_process_status != 'MI' or aleph_item_process_status != 'MS' or \
            aleph_item_process_status != 'Missing' or aleph_item_process_status != 'Misshelved':

        if aleph_item_process_status == 'OR' or aleph_item_process_status == 'On order':
            not_for_loan = '-1'
        elif aleph_item_process_status == 'GG' or aleph_item_process_status == 'In Process':
            not_for_loan = '-2'
        elif aleph_item_process_status == 'NL' or aleph_item_process_status == 'Undeliverable':
            not_for_loan = '-3'
        elif aleph_item_process_status == 'BD' or aleph_item_process_status == 'Binding':
            not_for_loan = '-4'
        elif aleph_item_process_status == 'CA' or aleph_item_process_status == 'Cancelled':
            not_for_loan = '-5'
        elif aleph_item_process_status == 'OI' or aleph_item_process_status == 'Order initiat.':
            not_for_loan = '-1'
        elif aleph_item_process_status == 'NA' or aleph_item_process_status == 'Not Arrived':
            not_for_loan = '-6'
        elif aleph_item_process_status == 'NP' or aleph_item_process_status == 'Not published':
            not_for_loan = '-7'
    elif aleph_item_status == '04':
        not_for_loan = '2'

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Field No. %s: 952$7 = '%s', valid 'Not for loan' found.", thesaurus_field_counter, not_for_loan)

    return not_for_loan


def map_restrictions(subfield_952_c):
    restricted = '0'

    if subfield_952_c == 'RARA' or subfield_952_c == 'RARAH':
        restricted = '1'

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Field No. %s: 952$5 = '%s', valid 'Restrictions' found.", thesaurus_field_counter, restricted)

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
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Field No. %s: 952$3 = '%s', valid 'Materials specified' copied from 300$e and "
                                     "300$3.", thesaurus_field_counter, materials_specified)
                else:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Field No. %s: 952$3 = '%s', "
                                     "no valid 'Materials specified' available from 300$e combined with 300$3!",
                                     thesaurus_field_counter, materials_specified)
            elif 'e' in field_300:
                subfield_300_e = field_300['e']
                if 1 > len(subfield_300_e) > 65535:
                    materials_specified = subfield_300_e
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Field No. %s: 952$3 = '%s', valid 'Materials specified' copied from 300$e.",
                                     thesaurus_field_counter, materials_specified)
                else:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Field No. %s: 952$3 = '%s', no valid 'Materials specified' available from 300$e!",
                                     thesaurus_field_counter, materials_specified)
            else:
                subfield_300_3 = field_300['3']
                if 1 > len(subfield_300_3) > 65535:
                    materials_specified = subfield_300_3
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Field No. %s: 952$3 = '%s', valid 'Materials specified' copied from 300$3.",
                                     thesaurus_field_counter, materials_specified)
                else:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Field No. %s: 952$3 = '%s', no valid 'Materials specified' available from 300$3!",
                                     thesaurus_field_counter, materials_specified)
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Field No. %s: 952$3 = '%s', no valid 'Materials specified' in 300$e and 300$3 found!",
                             thesaurus_field_counter, materials_specified)

    return materials_specified


def map_materials_specified(subfield_952_3):
    if 1 > len(subfield_952_3) > 65535:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$3 = '%s', no valid 'Materials specified' found!",
                         thesaurus_field_counter, subfield_952_3)

        return None
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$3 = '%s', valid 'Materials specified' found.",
                         thesaurus_field_counter, subfield_952_3)

        return subfield_952_3


def map_classification_source():
    classification_source = 'z'
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Field No. %s: 952$2 = '%s', valid 'Classification source' found.",
                     thesaurus_field_counter, classification_source)

    return classification_source


def map_lost_status(subfield_952_1):
    lost_status = '0'

    if subfield_952_1 == 'MI' or subfield_952_1 == 'MS' or \
            subfield_952_1 == 'Missing' or subfield_952_1 == 'Misshelved':

        lost_status = '1'

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Field No. %s: 952$1 = '%s', valid 'Lost status' found.", thesaurus_field_counter, lost_status)

    return lost_status


def map_public_note(subfield_952_z):
    if 1 > len(subfield_952_z) > 16777215:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$z = '%s', no valid 'Public note' found!",
                         thesaurus_field_counter, subfield_952_z)

        return None
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$z = '%s', valid 'Public note' found.",
                         thesaurus_field_counter, subfield_952_z)

        return subfield_952_z


def map_item_type(subfield_952_y):
    item_type = None

    if subfield_952_y is None:
        logger.error("Field No. %s: No required subfield 'y' found!", thesaurus_field_counter)
    else:
        item_type = marc_mappings.map_material(subfield_952_y)

        if item_type is None:
            logger.error("Field No. %s: 952$y = '%s', no valid 'Item type' code found!",
                         thesaurus_field_counter, subfield_952_y)
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Field No. %s: 952$y = '%s', valid 'Item type' code found.",
                             thesaurus_field_counter, item_type)

    return item_type


def map_nonpublic_note(subfield_952_x):
    if 1 > len(subfield_952_x) > 16777215:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$x = '%s', no valid 'Nonpublic note' found!",
                         thesaurus_field_counter, subfield_952_x)

        return None
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$x = '%s', valid 'Nonpublic note' found.",
                         thesaurus_field_counter, subfield_952_x)

        return subfield_952_x


def map_copy_number(subfield_952_t):
    if 1 > len(subfield_952_t) > 32:
        # logger.error("Aleph 'copy number' length exceeds Koha 'copy number' length!\n")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$t = '%s', no valid 'Copy number' found!",
                         thesaurus_field_counter, subfield_952_t)

        return None
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$t = '%s', valid 'Copy number' found.",
                         thesaurus_field_counter, subfield_952_t)

        return subfield_952_t


def map_barcode(subfield_952_p):
    if 1 > len(subfield_952_p) > 20:
        logger.error("Aleph 'barcode' length exceeds Koha 'Barcode' length!\n")
        logger.warning("Field No. %s: 952$p = '%s', no valid 'Barcode' found!",
                       thesaurus_field_counter, subfield_952_p)

        return None
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$p = '%s', valid 'Barcode' found.",
                         thesaurus_field_counter, subfield_952_p)

        return subfield_952_p


def map_call_number(subfield_952_o):
    if 1 > len(subfield_952_o) > 255:
        # logger.error("Length of 'call number' not in between 1 and 255!\n")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$o = '%s', no valid 'Call number' found!",
                         thesaurus_field_counter, subfield_952_o)

        return None
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$o = '%s', valid 'Call number' found.",
                         thesaurus_field_counter, subfield_952_o)

        return subfield_952_o


def map_inventory_number(subfield_952_i):
    if 1 > len(subfield_952_i) > 32:
        # logger.error("Aleph 'inventory number' length exceeds Koha 'stock number' length!\n")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$i = '%s', no valid 'Inventory number' found!",
                         thesaurus_field_counter, subfield_952_i)

        return None
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$i = '%s', valid 'Inventory number' found.",
                         thesaurus_field_counter, subfield_952_i)

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


def get_calculated_purchase_price(barcode):
    global ALEPH_ITEM_PRICE_LIST
    purchase_price = None

    if barcode in ALEPH_ITEM_PRICE_LIST:
        return ALEPH_ITEM_PRICE_LIST[barcode]

    return purchase_price


def map_purchase_price(subfield_952_g, subfield_952_p):
    if subfield_952_g is None:
        purchase_price = get_calculated_purchase_price(subfield_952_p)
    else:
        purchase_price = format_purchase_price(subfield_952_g)

    if purchase_price is None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$g = '%s', no valid 'Purchase price' found!",
                         thesaurus_field_counter, subfield_952_g)
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$g = '%s', valid 'Purchase price' found.",
                         thesaurus_field_counter, purchase_price)

    return purchase_price


def map_aleph_vendor_code(aleph_z70_vendor_code):
    global ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING

    if aleph_z70_vendor_code in ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING:
        return ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING[aleph_z70_vendor_code]
    else:
        return None


def map_source_of_acquisition(subfield_952_e):
    source_of_acquisition = map_aleph_vendor_code(subfield_952_e)

    if source_of_acquisition is None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$e = '%s', no valid 'Source of aquisition' found!",
                         thesaurus_field_counter, subfield_952_e)
        pass
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$e = '%s', valid 'Source of aquisition' found.",
                         thesaurus_field_counter, source_of_acquisition)
        pass

    return source_of_acquisition


def map_aleph_date_field(marc_field_code, marc_subfield_code, field_name, field_value):
    date = dates_helper.process_aleph_date(field_value)

    if date is None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: %s$%s = '%s', no valid '%s' found!",
                         thesaurus_field_counter, marc_field_code, marc_subfield_code, field_value, field_name)
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: %s$%s = '%s', valid '%s' found.",
                         thesaurus_field_counter, marc_field_code, marc_subfield_code, date, field_name)

    return date


def map_shelving_location_code(subfield_952_c, koha_library_code):
    shelving_location_code = marc_mappings.map_shelving_location(subfield_952_c, koha_library_code)

    if shelving_location_code is None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$c = '%s', no valid 'Shelving location' found!",
                         thesaurus_field_counter, subfield_952_c)
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: 952$c = '%s', valid 'Shelving location' found.",
                         thesaurus_field_counter, shelving_location_code)

    return shelving_location_code


def map_holding_library(subfield_952_b):
    holding_library = None

    if subfield_952_b is None:
        logger.error("Field No. %s: No required subfield 'b' found!", thesaurus_field_counter)
    else:
        holding_library = library_keys.map_aleph_key(subfield_952_b)
        if holding_library is None:
            logger.error("Field No. %s: 952$b = '%s', no valid 'Holding library' code found!",
                         thesaurus_field_counter, subfield_952_b)
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Field No. %s: 952$b = '%s', valid 'Holding library' code found.",
                             thesaurus_field_counter, holding_library)

    return holding_library


def map_owning_library(subfield_952_a):
    owning_library = None

    if subfield_952_a is None:
        logger.error("Field No. %s: No required subfield 'a' found!", thesaurus_field_counter)
    else:
        owning_library = library_keys.map_aleph_key(subfield_952_a)
        if owning_library is None:
            logger.error("Field No. %s: 952$a = '%s' , no valid 'Owning library' code found!",
                         thesaurus_field_counter, subfield_952_a)
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Field No. %s: 952$a = '%s', valid 'Owning library' code found.",
                             thesaurus_field_counter, owning_library)

    return owning_library


def check_required_subfields(field_952):
    is_success = False

    if all(subfields in field_952 for subfields in ('a', 'b', 'y')):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: All required subfieds 'a', 'b', and 'y' found.", thesaurus_field_counter)
        is_success = True
    elif 'y' in field_952 and ('a' or 'b' in field_952):
        if 'a' not in field_952:
            field_952.add_subfield('a', field_952['b'])
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Field No. %s: Required subfield 'a' not found! Copy subfield 'b' into subfield 'a': 952$a = %s",
                    thesaurus_field_counter, field_952['a']
                )
        if 'b' not in field_952:
            field_952.add_subfield('b', field_952['a'])
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Field No. %s: Required subfield 'b' not found! Copy subfield 'a' into subfield 'b': 952$b = %s",
                    thesaurus_field_counter, field_952['b']
                )
        is_success = True
    else:
        logger.error('Field No. %s: Neither required subfields 952$a and 952$b found nor required subfield 952$y!',
                     thesaurus_field_counter)

    return is_success


def get_aleph_item_price_list():
    oracle.open_connection()
    result = oracle.get_item_price_list()
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug('Item price list:\n%s', result)
    oracle.close_connection()

    return result


def get_barcode_to_zenon_id_mapping():
    result = {}

    oracle.open_connection()
    data_cursor = oracle.get_barcode_to_zenon_id_mapping()
    for query_result in data_cursor:

        blank_number = '0'*9
        value = str(query_result[1])

        result[query_result[0].strip()] = f'{blank_number[:-len(value)]}{value}'

    return result


def init():
    global ALEPH_ITEM_PRICE_LIST
    global ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING
    global BARCODE_TO_ZENON_ID_MAPPING

    if not ALEPH_ITEM_PRICE_LIST:
        logger.info('initializing ALEPH_ITEM_PRICE_LIST')
        query_results = get_aleph_item_price_list()
        for barcode, price in query_results:
            if barcode in ALEPH_ITEM_PRICE_LIST:
                logger.warning(f'Already mappend price for barcode {barcode}: {ALEPH_ITEM_PRICE_LIST[barcode]}, '
                               f'new value: {price}.')

            ALEPH_ITEM_PRICE_LIST[barcode] = price

    oracle.open_connection()

    if not ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING:
        logger.info('initializing ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING')
        query_results = oracle.get_z70()
        for query_result in query_results:
            if query_result[0].strip() in ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING:
                logger.warning(f'Already mapped bookseller name for Aleph vendor code {query_result[0].strip()}: '
                               f'{ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING[query_result[0].strip()]}, '
                               f'new name: {query_result[7].strip()}.')

            ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING[query_result[0].strip()] = query_result[7].strip()

    if not BARCODE_TO_ZENON_ID_MAPPING:
        logger.info('initializing BARCODE_TO_ZENON_ID_MAPPING')
        BARCODE_TO_ZENON_ID_MAPPING = get_barcode_to_zenon_id_mapping()

    if len(ALEPH_ITEM_PRICE_LIST) < 1:
        exit("Calculated aleph item price list ist empty!")

    if len(ALEPH_VENDOR_CODE_KOHA_BOOKSELLER_NAME_MAPPING) < 1:
        exit("'AQBOOKSELLERS' table is empty!")

    if len(BARCODE_TO_ZENON_ID_MAPPING) < 1:
        exit("'BARCODE_TO_ZENON_ID_MAPPING' is empty!")


def prepare_marc(record):
    global thesaurus_field_counter
    global holding_field_max

    items_kept_based_on_barcode = 0
    items_deleted_based_on_barcode = 0

    record_error_no = 0
    is_record_format_error = False
    is_record_format_warning = False
    is_record_format_info = False
    is_record_format_debugging = False

    init()

    logger.info("Processing holding information of Marc record: '%s' ...", record.leader)

    marc_holding_fields = record.get_fields(HOLDING_FIELD_CODE)

    holding_field_count = len(marc_holding_fields)
    logger.info("%s holding field(s) found.", holding_field_count)
    logger.info("Previous holding field max count: %s", holding_field_max[1])

    if holding_field_count > holding_field_max[1]:
        holding_field_max[0] = record.leader
        holding_field_max[1] = holding_field_count

    holding_field_counter = 1
    for field_952 in marc_holding_fields:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: %s", holding_field_counter, field_952)

        if check_required_subfields(field_952):

            subfield_952_p = field_952['p']
            # '952$p' Barcode (required for circulation)
            if subfield_952_p is None:
                logger.warning("Field No. %s: No required subfield 'p' found!", holding_field_counter)
                record_error_no += 1
            else:
                koha_barcode = map_barcode(subfield_952_p)
                if koha_barcode is None:
                    logger.warning("Field No. %s: Skipping subfield 'p' in marc field %s",
                                   holding_field_counter, field_952)
                    field_952.delete_subfield('p')
                    is_record_format_error = True
                    record_error_no += 1
                else:
                    if koha_barcode in BARCODE_TO_ZENON_ID_MAPPING:
                        barcode_zenon_id = BARCODE_TO_ZENON_ID_MAPPING[koha_barcode]
                        record_zenon_id = record['001'].data
                        if barcode_zenon_id == record_zenon_id:
                            items_kept_based_on_barcode += 1
                            field_952['p'] = koha_barcode
                        else:
                            items_deleted_based_on_barcode += 1
                            record.remove_field(field_952)
                            continue

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
                koha_date_acquired = map_aleph_date_field(HOLDING_FIELD_CODE, date_acquired_subfield_code,
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
            koha_purchase_prise = map_purchase_price(subfield_952_g, subfield_952_p)
            if koha_purchase_prise is None:
                logger.info("Field No. %s: Skipping subfield 'g' = %s", holding_field_counter, subfield_952_g)
                field_952.delete_subfield('g')
            else:
                if subfield_952_g is not None:
                    field_952['g'] = koha_purchase_prise
                else:
                    field_952.add_subfield('g', koha_purchase_prise)
                    logger.info("Field No. %s: Added subfield 'g' = '%s' (barcode: %s)",
                                holding_field_counter, koha_purchase_prise, subfield_952_p)

            # '952$h' Serial enumeration
            serial_enumeration_subfield_code = 'h'
            subfield_952_h = field_952[serial_enumeration_subfield_code]
            map_aleph_string_field(
                HOLDING_FIELD_CODE, serial_enumeration_subfield_code, 'Z30_ENUMERATION', subfield_952_h)

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
            koha_not_for_loan = map_not_for_loan(subfield_952_7, subfield_952_1)
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
            map_aleph_string_field(HOLDING_FIELD_CODE, order_number_subfield_code, 'Z30_ORDER_NUMBER', subfield_952_A)

            # '952$C' Umlauf-Notiz
            note_circulation_subfield_code = 'C'
            subfield_952_C = field_952[note_circulation_subfield_code]
            map_aleph_string_field(HOLDING_FIELD_CODE, note_circulation_subfield_code,
                                   'Z30_NOTE_CIRCULATION', subfield_952_C)

            # '952$D' Beschreibung
            description_subfield_code = 'D'
            subfield_952_D = field_952[description_subfield_code]
            map_aleph_string_field(HOLDING_FIELD_CODE, description_subfield_code, 'Z30_DESCRIPTION', subfield_952_D)

            # '952$E' Erwartet zum (Zeitschriftenheft) Datum
            expected_arrival_date_subfield_code = 'E'
            subfield_952_E = field_952[expected_arrival_date_subfield_code]
            if subfield_952_E is not None:
                expected_arrival_date = map_aleph_date_field(HOLDING_FIELD_CODE, expected_arrival_date_subfield_code,
                                                             'Z30_EXPECTED_ARRIVAL_DATE', subfield_952_E)
                if expected_arrival_date is None:
                    logger.info("Field No. %s: Skipping subfield '%s' = %s",
                                holding_field_counter, expected_arrival_date_subfield_code, subfield_952_E)
                    field_952.delete_subfield(expected_arrival_date_subfield_code)
                else:
                    field_952[expected_arrival_date_subfield_code] = expected_arrival_date

            # '952$H' Jahreszählung bei Zeitschriftenheften
            chronological_subfield_code = 'H'
            subfield_952_H = field_952[chronological_subfield_code]
            map_aleph_string_field(
                HOLDING_FIELD_CODE, chronological_subfield_code, 'Z30_CHRONOLOGICAL_I', subfield_952_H)

            # '952$J' Exemplarstatus
            item_status_subfield_code = 'J'
            subfield_952_J = field_952[item_status_subfield_code]
            map_aleph_string_field(HOLDING_FIELD_CODE, item_status_subfield_code, 'Z30_ITEM_STATUS', subfield_952_J)

            # '952$O' 2. Signatur
            call_no_2_subfield_code = 'O'
            subfield_952_O = field_952[call_no_2_subfield_code]
            map_aleph_string_field(HOLDING_FIELD_CODE, call_no_2_subfield_code, 'Z30_CALL_NO_2', subfield_952_O)

            # '952$P' Erfassungsdatum
            open_date_subfield_code = 'P'
            subfield_952_P = field_952[open_date_subfield_code]
            if subfield_952_P is not None:
                open_date = map_aleph_date_field(HOLDING_FIELD_CODE, open_date_subfield_code,
                                                 'Z30_OPEN_DATE', subfield_952_P)
                if open_date is None:
                    logger.info("Field No. %s: Skipping subfield '%s' = %s",
                                holding_field_counter, open_date_subfield_code, subfield_952_P)
                    field_952.delete_subfield(open_date_subfield_code)
                else:
                    field_952[open_date_subfield_code] = open_date

            # '952$S' Exemplar-Geschäftsgang-Status
            item_process_status_subfield_code = 'S'
            subfield_952_S = field_952[item_process_status_subfield_code]
            map_aleph_string_field(HOLDING_FIELD_CODE, item_process_status_subfield_code,
                                   'Z30_ITEM_PROCESS_STATUS ', subfield_952_S)

            # '952$T' Statistikwerte
            item_statistic_subfield_code = 'T'
            subfield_952_T = field_952[item_statistic_subfield_code]
            if subfield_952_T is not None:
                item_statistic = map_aleph_item_statistic(subfield_952_T, subfield_952_A)
                if item_statistic is None:
                    logger.info("Field No. %s: Skipping subfield '%s' = %s",
                                holding_field_counter, item_statistic_subfield_code, item_statistic)
                    field_952.delete_subfield(item_statistic_subfield_code)
                else:
                    field_952[item_statistic_subfield_code] = item_statistic

            # '952$U' Änderungsdatum
            update_date_subfield_code = 'U'
            subfield_952_U = field_952[update_date_subfield_code]
            if subfield_952_U is not None:
                update_date = map_aleph_date_field(HOLDING_FIELD_CODE, update_date_subfield_code,
                                                   'Z30_UPDATE_DATE', subfield_952_U)
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

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Field No. %s: %s", holding_field_counter, field_952)
        holding_field_counter += 1

    if is_record_format_error:
        logger.error('In Record:\n%s', record)
    elif is_record_format_warning:
        logger.warning('In Record:\n%s', record)
    elif is_record_format_info:
        logger.info('In Record:\n%s', record)
    elif is_record_format_debugging:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('In Record:\n%s', record)

    logger.info('%s record error(s) found.', record_error_no)
    logger.info("Marc Record '%s' process completed!\n", record.leader)

    return record_error_no, items_kept_based_on_barcode, items_deleted_based_on_barcode
