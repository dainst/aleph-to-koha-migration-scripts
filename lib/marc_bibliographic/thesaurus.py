import logging
import re

from pymarc import Field
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

THESAURUS_FIELD_CODE = '999'
NOTATION_651_INCLUDE_LIST: List[str] = [
    'xAntWirtschOrt',
    'xArchitBauKirch.+',
    'xArchitKgLandsch',
    'xEpigrGrEWG.+',
    'xEpigrLatEWG.+',
    'xFrMAGeb.+',
    'xGefFund.+',
    'xGefTonAmphFundl.+',
    'xGefTonGebr.+',
    'xGefTonTSArret',
    'xGefTonTSDonau',
    'xGefTonTSGall',
    'xGefTonTSGall.+',
    'xGefTonTSIt',
    'xGefTonTSSp',
    'xGeschBevölkOrt',
    'xJuraRömVerwPSeinz',
    'xKgLandsch',
    'xMalWandHaus.+',
    'xMosTess.+',
    'xMusSlgAukt',
    'xMusSlgAukt.+',
    'xMusSlgAusst.+',
    'xMusSlgMusLand.+',
    'xMusSlgMusOrt.+',
    'xNumFund.+',
    'xNumGrMünzst',
    'xNumRömMünzst',
    'xNumRömProv',
    'xOrGeschIran',
    'xOrGeschMes',
    'xOrGeschSyr',
    'xOrReligIran',
    'xOrReligMes',
    'xOrReligSyr',
    'xPlastKgLandsch',
    'xReligChrOrt',
    'xReligOrt',
    'xReligOrtEinz.+',
    'xRkAlp',
    'xRkAnat',
    'xRkArab'
    'xRkArm',
    'xRkBakt',
    'xRkEdess',
    'xRkFr',
    'xRkGand',
    'xRkIber',
    'xRkKauk',
    'xRkKommag',
    'xRkKyp',
    'xRkM-As',
    'xRkMak',
    'xRkN-Afr',
    'xRkNub',
    'xRkPalm'
    'xRkSchwarzm',
    'xRkSO-Eur',
    'xRkSyr',
    'xTopKart.+',
    # 'xTopLand',
    'xTopLand.+',
    'xTopRAIAth',
    'xTopRAIAth.+',
    'xTopRAIIstan',
    'xTopRAIIstan.+',
    'xTopRAIRom',
    'xTopRAIRom.+',
    'xTopSchlachtf',
    'xTopSiedl.+',
    'xTopWeg.+',
    'xVg.+'
    'zEuropSüdeuItali.+',
    'zTopog.+',
    '3\.00\.01',
    '3\.00\.01\.01',
    '3\.00\.01\.01.+',
    '3\.00\.01\.02',
    '3\.00\.01\.02.+',
    '4\.02',
    '4\.02\..+'
]
NOTATION_651_EXCLUDE_LIST: List[str] = [
    'xEpigrGrEWGAllg',
    'xEpigrGrEWGMehr',
    'xEpigrLatEWGAllg',
    'xEpigrLatEWGMehr',
    'xFrMAGebMehr',
    'xGefTonAmphFundlMehr',
    'xGefTonGebrMehr',
    'xGefTonTSGallMehr',
    'xMalWandHausMehr',
    'xMosTessMehr',
    'xTopKartUmf',
    'xTopWegAllg',
    'xVgImport',
    'xVgUmf'
]


def map_thesaurus_on_marc_650(marc_thesaurus_field):
    thesaurus_subfield_a = marc_thesaurus_field['a']
    thesaurus_subfield_e = marc_thesaurus_field['e']
    thesaurus_subfield_m = marc_thesaurus_field['m']
    thesaurus_subfield_r = marc_thesaurus_field['r']
    thesaurus_subfield_1 = marc_thesaurus_field['1']
    is_651_notation_match = False
    field_650 = None

    if \
            thesaurus_subfield_a is not None and \
            thesaurus_subfield_1 is not None and \
            (
                thesaurus_subfield_e is None or
                thesaurus_subfield_m is None or
                thesaurus_subfield_r is None
            ):
        for incl_651_reg_exp in NOTATION_651_INCLUDE_LIST:
            incl_651_match = re.match(incl_651_reg_exp, thesaurus_subfield_1)
            if incl_651_match is not None:
                is_651_notation_match = True
                for excl_651_reg_exp in NOTATION_651_EXCLUDE_LIST:
                    excl_651_match = re.match(excl_651_reg_exp, thesaurus_subfield_1)
                    if excl_651_match is not None:
                        is_651_notation_match = False
                        break
                break

        if not is_651_notation_match:
            field_650 = Field(tag='650', indicators=['\\', '\\'])
            field_650.add_subfield('a', thesaurus_subfield_a)
            field_650.add_subfield('2', thesaurus_subfield_1)

    return field_650


def map_thesaurus_on_marc_651(marc_thesaurus_field):
    thesaurus_subfield_a = marc_thesaurus_field['a']
    thesaurus_subfield_e = marc_thesaurus_field['e']
    thesaurus_subfield_m = marc_thesaurus_field['m']
    thesaurus_subfield_r = marc_thesaurus_field['r']
    thesaurus_subfield_1 = marc_thesaurus_field['1']
    is_651_notation_match = False
    field_651 = None

    if \
            thesaurus_subfield_a is not None and \
            (
                thesaurus_subfield_e is not None or
                thesaurus_subfield_m is not None or
                thesaurus_subfield_r is not None or
                thesaurus_subfield_1 is not None
            ):

        if thesaurus_subfield_1 is not None:
            logger.info("999$1 = " + thesaurus_subfield_1)
            for incl_651_reg_exp in NOTATION_651_INCLUDE_LIST:
                incl_651_match = re.match(incl_651_reg_exp, thesaurus_subfield_1)
                if incl_651_match is not None:
                    logger.info("incl_651_match = " + str(incl_651_match))
                    is_651_notation_match = True
                    for excl_651_reg_exp in NOTATION_651_EXCLUDE_LIST:
                        excl_651_match = re.match(excl_651_reg_exp, thesaurus_subfield_1)
                        if excl_651_match is not None:
                            logger.info("excl_651_match = " + str(excl_651_match))
                            is_651_notation_match = False
                            break
                    break

        if thesaurus_subfield_1 is None or is_651_notation_match:
            field_651 = Field(tag='651', indicators=['\\', '\\'])

            if thesaurus_subfield_e is not None:
                field_651.add_subfield('a', thesaurus_subfield_e)

            if thesaurus_subfield_m is not None:
                field_651.add_subfield('a', thesaurus_subfield_m)

            if thesaurus_subfield_r is not None:
                field_651.add_subfield('a', thesaurus_subfield_r)

            if thesaurus_subfield_a is not None:
                if thesaurus_subfield_e is not None or \
                        thesaurus_subfield_m is not None or \
                        thesaurus_subfield_r is not None:
                    field_651.add_subfield('g', thesaurus_subfield_a)
                else:
                    field_651.add_subfield('a', thesaurus_subfield_a)

            if is_651_notation_match:
                field_651.add_subfield('2', thesaurus_subfield_1)

    return field_651


def map_thesaurus(record):
    record_error_no = 0
    is_record_format_error = False
    marc_thesaurus_fields = record.get_fields(THESAURUS_FIELD_CODE)
    thesaurus_field_count = len(marc_thesaurus_fields)
    logger.info("%s thesaurus field(s) found.", thesaurus_field_count)

    thesaurus_field_counter = 1
    for marc_thesaurus_field in marc_thesaurus_fields:
        logger.debug("Field No. %s: %s", thesaurus_field_counter, marc_thesaurus_field)
        field_650 = map_thesaurus_on_marc_650(marc_thesaurus_field)
        field_651 = map_thesaurus_on_marc_651(marc_thesaurus_field)

        if field_650 is not None and field_651 is not None:
            logger.error("Field No. %s: No unique mapping!\nThesaurus field %s is mapped on:\n%s and\n%s)",
                         thesaurus_field_counter, marc_thesaurus_field, field_650, field_651)
            is_record_format_error = True
            record_error_no += 1
        else:
            if field_650 is not None:
                record.add_field(field_650)
                logger.debug("Field No. %s: %s", thesaurus_field_counter, field_650)

            if field_651 is not None:
                record.add_field(field_651)
                logger.debug("Field No. %s: %s", thesaurus_field_counter, field_651)

        thesaurus_field_counter += 1

    if is_record_format_error:
        logger.error('Error in Record:\n%s', record)

    return record_error_no


def prepare_marc(record):
    logger.info("Processing thesaurus information of Marc record: '%s' ...", record.leader)

    record_error_no = map_thesaurus(record)
    record.remove_fields(THESAURUS_FIELD_CODE)

    logger.info("Marc Record '%s' process completed!\n", record.leader)

    return record_error_no
