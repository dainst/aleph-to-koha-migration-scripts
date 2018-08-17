import logging
import re

from pymarc import Field, Record
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

THESAURUS_FIELD_CODE: str = '999'
NOTATION_600_LIST: List[str] = [
    'xArchitKgArchitektEinz',
    'xBthChrBen',
    'xBthGMythBen',
    'xGefTonMTEinz',
    'xGeschProsEinz.+',
    'xMalKgMaler',
    'xNumRömHerrsch',
    'xPlastKgBildhEinz',
    'xPlastRundplGruppGMyth',
    'xPlastRundplKopfGMyth',
    'xPlastRundplStGMyth',
    'xPortrBen',
    'xReligEP',
    'xReligChrPersEinz',
    'xReligGMythBen.+',
    'xPersEP.+',
    'xSarkSteinBthGMyth'
    'xSlbdEinzVerf.+',
    'xSlbdFestschrA-G',
    'xSlbdFestschrH-P',
    'xSlbdFestschrQ-Z',
    'yForschPerso.+',
    'yRGKArch02 - Gesch.+',
    'yRGKArch02 - Perso.+',
    'yRGKArch08 - GeselReligGötte.+',
    'yRGKArch08 - HistoNumisPräguRepubPräge.+',
    'yRGKArch08 - HistoProsoEinze.+',
    'yRGKArch09 - GeselKunstIkonoProfaMenscPortr.+',
    'yRGKArch09 - GeselKunstIkonoSakraMytho.+',
    'yRGKArch09 - GeselReligGötte.+',
    'yRGKArch09 - GeselReligKulteHerrsHerrs.+',
    'yRGKArch09 - HistoNumisPräguRömisPräge.+',
    'yRGKArch10 - GeselKunstIkonoProfaMenscPortr.+',
    'yRGKArch10 - GeselKunstIkonoSakraMythoMytho.+',
    'yRGKArch10 - GeselReligGötte.+',
    'yRGKArch10 - GeselReligKulteHerrs.+',
    'yRGKArch10 - GeselReligReligChrisHäres.+',
    'yRGKArch10 - GeselReligReligChrisHeili.+',
    'yRGKArch10 - HistoNumisPräguRömisPräge.+',
    'yRGKArch10 - HistoProsoEinze.+',
    'yRGKArch11 - GeselReligKulteGötte.+',
    'yRGKArch11 - GeselReligReligChrisHeiliHeili.+',
    'yRGKArch11 - GeselReligReligChrisHäres.+',
    'yRGKArch11 - HistoNumisPräguPräge.+',
    'yRGKArch11 - HistoProsoEinze.+',
    'yRGKArch12 - GeselKunstIkonoPortr.+',
    'yRGKArch12 - GeselKunstKünst.+',
    'yRGKArch12 - GeselReligKulteGötte.+',
    'yRGKArch12 - GeselReligReligChrisHeiliHeili.+',
    'yRGKArch12 - HistoOnomaPersoNamen.+',
    'yRGKArch12 - HistoProsoEinze.+',
    'yRGKMusMuseeNachl.+',
    'yRGKNachsBibli.+',
    'zFests.+',
    '3\.00\.03\.02',
    '3\.01\.04'
]
NOTATION_600_MYTH_SUB_LIST: List[str] = [
    'xBthGMythBen',
    'xPlastRundplGruppGMyth',
    'xPlastRundplKopfGMyth',
    'xPlastRundplStGMyth',
    'xSarkSteinBthGMyth',
    'yRGKArch08 - GeselReligGötte.+',
    'yRGKArch09 - GeselKunstIkonoSakraMytho.+',
    'yRGKArch09 - GeselReligGötte.+',
    'yRGKArch10 - GeselKunstIkonoSakraMythoMytho.+',
    'yRGKArch10 - GeselReligGötte.+',
    'yRGKArch11 - GeselReligKulteGötte.+',
    'yRGKArch12 - GeselReligKulteGötte.+'
]
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
    '3\.00\.01\.01\..+',
    '3\.00\.01\.02',
    '3\.00\.01\.02\..+',
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
MYTH_NOTATION_SUBFIELD_C: str = "(Mythological character)"


def map_thesaurus_on_marc_600(marc_thesaurus_field: Field) -> Field:
    thesaurus_subfield_a: str = marc_thesaurus_field['a']
    thesaurus_subfield_e: str = marc_thesaurus_field['e']
    thesaurus_subfield_m: str = marc_thesaurus_field['m']
    thesaurus_subfield_r: str = marc_thesaurus_field['r']
    thesaurus_subfield_1: str = marc_thesaurus_field['1']
    is_600_notation_match: bool = False
    is_600_myth_notation_match: bool = False
    field_600: Field = None

    if thesaurus_subfield_a is not None and thesaurus_subfield_1 is not None:
        logger.debug("999$1 = " + thesaurus_subfield_1)

        for notation_600_reg_exp in NOTATION_600_LIST:
            notation_600_match = re.match(notation_600_reg_exp, thesaurus_subfield_1)

            if notation_600_match is not None:
                logger.debug("notation_600_match = " + str(notation_600_match))
                is_600_notation_match = True

                for notation_600_myth_reg_exp in NOTATION_600_MYTH_SUB_LIST:
                    notation_600_myth_match = re.match(notation_600_myth_reg_exp, thesaurus_subfield_1)

                    if notation_600_myth_match is not None:
                        logger.debug("notation_600_myth_match = " + str(notation_600_myth_match))
                        is_600_myth_notation_match = True
                        break
                break

        if is_600_notation_match:
            field_600 = Field(tag='600', indicators=['\\', '\\'])

            if thesaurus_subfield_e is not None or \
                    thesaurus_subfield_m is not None or \
                    thesaurus_subfield_r is not None:

                if thesaurus_subfield_e is not None:
                    field_600.add_subfield('a', thesaurus_subfield_e)

                if thesaurus_subfield_m is not None:
                    field_600.add_subfield('a', thesaurus_subfield_m)

                if thesaurus_subfield_r is not None:
                    field_600.add_subfield('a', thesaurus_subfield_r)

                if is_600_myth_notation_match:
                    field_600.add_subfield('c', MYTH_NOTATION_SUBFIELD_C)

                field_600.add_subfield('g', thesaurus_subfield_a)

            else:
                field_600.add_subfield('a', thesaurus_subfield_a)

                if is_600_myth_notation_match:
                    field_600.add_subfield('c', MYTH_NOTATION_SUBFIELD_C)

            field_600.add_subfield('2', thesaurus_subfield_1)

    return field_600


def map_thesaurus_on_marc_650(marc_thesaurus_field: Field) -> Field:
    thesaurus_subfield_a: str = marc_thesaurus_field['a']
    thesaurus_subfield_e: str = marc_thesaurus_field['e']
    thesaurus_subfield_m: str = marc_thesaurus_field['m']
    thesaurus_subfield_r: str = marc_thesaurus_field['r']
    thesaurus_subfield_1: str = marc_thesaurus_field['1']
    is_651_notation_match: bool = False
    field_650: Field = None

    if thesaurus_subfield_a is not None and thesaurus_subfield_1 is not None:
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

            if thesaurus_subfield_e is not None or \
                    thesaurus_subfield_m is not None or \
                    thesaurus_subfield_r is not None:

                if thesaurus_subfield_e is not None:
                    field_650.add_subfield('a', thesaurus_subfield_e)

                if thesaurus_subfield_m is not None:
                    field_650.add_subfield('a', thesaurus_subfield_m)

                if thesaurus_subfield_r is not None:
                    field_650.add_subfield('a', thesaurus_subfield_r)

                field_650.add_subfield('g', thesaurus_subfield_a)

            else:
                field_650.add_subfield('a', thesaurus_subfield_a)

            field_650.add_subfield('2', thesaurus_subfield_1)

    return field_650


def map_thesaurus_on_marc_651(marc_thesaurus_field: Field) -> Field:
    thesaurus_subfield_a: str = marc_thesaurus_field['a']
    thesaurus_subfield_e: str = marc_thesaurus_field['e']
    thesaurus_subfield_m: str = marc_thesaurus_field['m']
    thesaurus_subfield_r: str = marc_thesaurus_field['r']
    thesaurus_subfield_1: str = marc_thesaurus_field['1']
    is_651_notation_match: bool = False
    field_651: Field = None

    if thesaurus_subfield_a is not None and thesaurus_subfield_1 is not None:
        logger.debug("999$1 = " + thesaurus_subfield_1)

        for incl_651_reg_exp in NOTATION_651_INCLUDE_LIST:
            incl_651_match = re.match(incl_651_reg_exp, thesaurus_subfield_1)

            if incl_651_match is not None:
                logger.debug("incl_651_match = " + str(incl_651_match))
                is_651_notation_match = True

                for excl_651_reg_exp in NOTATION_651_EXCLUDE_LIST:
                    excl_651_match = re.match(excl_651_reg_exp, thesaurus_subfield_1)

                    if excl_651_match is not None:
                        logger.debug("excl_651_match = " + str(excl_651_match))
                        is_651_notation_match = False
                        break
                break

        if is_651_notation_match:
            field_651 = Field(tag='651', indicators=['\\', '\\'])

            if thesaurus_subfield_e is not None or thesaurus_subfield_m is not None or thesaurus_subfield_r is not None:
                if thesaurus_subfield_e is not None:
                    field_651.add_subfield('a', thesaurus_subfield_e)

                if thesaurus_subfield_m is not None:
                    field_651.add_subfield('a', thesaurus_subfield_m)

                if thesaurus_subfield_r is not None:
                    field_651.add_subfield('a', thesaurus_subfield_r)

                field_651.add_subfield('g', thesaurus_subfield_a)

            else:
                field_651.add_subfield('a', thesaurus_subfield_a)

            field_651.add_subfield('2', thesaurus_subfield_1)

    return field_651


def map_thesaurus(record: Record) -> int:
    record_error_no: int = 0
    is_record_format_error: bool = False
    marc_thesaurus_fields: List[Field] = record.get_fields(THESAURUS_FIELD_CODE)
    thesaurus_field_count: int = len(marc_thesaurus_fields)
    logger.info("%s thesaurus field(s) found.", thesaurus_field_count)

    thesaurus_field_counter: int = 1
    for marc_thesaurus_field in marc_thesaurus_fields:
        logger.debug("Field No. %s: %s", thesaurus_field_counter, marc_thesaurus_field)
        field_650: Field = map_thesaurus_on_marc_650(marc_thesaurus_field)
        field_651: Field = map_thesaurus_on_marc_651(marc_thesaurus_field)

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


def prepare_marc(record: Record) -> int:
    logger.info("Processing thesaurus information of Marc record: '%s' ...", record.leader)

    record_error_no: int = map_thesaurus(record)
    record.remove_fields(THESAURUS_FIELD_CODE)

    logger.info("Marc Record '%s' process completed!\n", record.leader)

    return record_error_no
