import logging
import re

from pymarc import Field, Record
from typing import List, Tuple

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

THESAURUS_FIELD_CODE: str = '999'
NOTATION_600_TUPLE: Tuple[str] = (
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
)
NOTATION_600_MYTH_SUB_TUPLE: Tuple[str] = (
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
)
NOTATION_651_INCLUDE_TUPLE: Tuple[str] = (
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
)
NOTATION_651_EXCLUDE_TUPLE: Tuple[str] = (
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
)
MYTH_NOTATION_SUBFIELD_C: str = "(Mythological character)"


def map_thesaurus_on_marc_6xx(marc_thesaurus_field, mapping_field_nr: str) -> Field:
    is_600_myth_notation_match = False
    thesaurus_subfield_a: str = marc_thesaurus_field['a']
    thesaurus_subfield_e: str = marc_thesaurus_field['e']
    thesaurus_subfield_m: str = marc_thesaurus_field['m']
    thesaurus_subfield_r: str = marc_thesaurus_field['r']
    thesaurus_subfield_1: str = marc_thesaurus_field['1']
    field_6xx = Field(tag=mapping_field_nr, indicators=['\\', '\\'])

    if mapping_field_nr == '600':
        for notation_600_myth_reg_exp in NOTATION_600_MYTH_SUB_TUPLE:
            notation_600_myth_match = re.match(notation_600_myth_reg_exp, thesaurus_subfield_1)

            if notation_600_myth_match is not None:
                logger.debug("600_myth_match: %s (reg_exp='%s')",
                             str(notation_600_myth_match), notation_600_myth_reg_exp)
                is_600_myth_notation_match = True
            break

    if \
            thesaurus_subfield_e is not None or \
            thesaurus_subfield_m is not None or \
            thesaurus_subfield_r is not None:

        if thesaurus_subfield_e is not None:
            field_6xx.add_subfield('a', thesaurus_subfield_e)

        if thesaurus_subfield_m is not None:
            field_6xx.add_subfield('a', thesaurus_subfield_m)

        if thesaurus_subfield_r is not None:
            field_6xx.add_subfield('a', thesaurus_subfield_r)

        if is_600_myth_notation_match:
            field_6xx.add_subfield('c', MYTH_NOTATION_SUBFIELD_C)

        field_6xx.add_subfield('g', thesaurus_subfield_a)

    else:
        field_6xx.add_subfield('a', thesaurus_subfield_a)

        if is_600_myth_notation_match:
            field_6xx.add_subfield('c', MYTH_NOTATION_SUBFIELD_C)

    field_6xx.add_subfield('2', thesaurus_subfield_1)

    return field_6xx


def identify_mapping_field_nr(thesaurus_subfield_1: str) -> str:
    is_600_notation_match: bool = False
    is_651_notation_match: bool = False

    for notation_600_reg_exp in NOTATION_600_TUPLE:
        notation_600_match = re.match(notation_600_reg_exp, thesaurus_subfield_1)

        if notation_600_match is not None:
            logger.debug("600_match: %s (reg_exp='%s')", str(notation_600_match), notation_600_reg_exp)
            is_600_notation_match = True
            break

    for incl_651_reg_exp in NOTATION_651_INCLUDE_TUPLE:
        incl_651_match = re.match(incl_651_reg_exp, thesaurus_subfield_1)

        if incl_651_match is not None:
            logger.debug("651_incl_match: %s (reg_exp='%s')", str(incl_651_match), incl_651_reg_exp)
            is_651_notation_match = True

            for excl_651_reg_exp in NOTATION_651_EXCLUDE_TUPLE:
                excl_651_match = re.match(excl_651_reg_exp, thesaurus_subfield_1)

                if excl_651_match is not None:
                    logger.debug("651_excl_match: %s (reg_exp='%s')", str(excl_651_match), excl_651_reg_exp)
                    is_651_notation_match = False
                    break
            break

    if is_600_notation_match and is_651_notation_match:
        raise ValueError
    elif is_600_notation_match:
        return '600'
    elif is_651_notation_match:
        return '651'
    else:
        return '650'


def map_thesaurus(record: Record) -> int:
    record_error_no: int = 0
    is_record_format_error: bool = False
    marc_thesaurus_fields: List[Field] = record.get_fields(THESAURUS_FIELD_CODE)
    thesaurus_field_count: int = len(marc_thesaurus_fields)
    logger.info("%s thesaurus field(s) found.", thesaurus_field_count)

    thesaurus_field_counter: int = 1
    for marc_thesaurus_field in marc_thesaurus_fields:
        logger.debug("Field No. %s: %s", thesaurus_field_counter, marc_thesaurus_field)
        thesaurus_subfield_a: str = marc_thesaurus_field['a']
        thesaurus_subfield_1: str = marc_thesaurus_field['1']

        if thesaurus_subfield_a is not None and thesaurus_subfield_1 is not None:
            try:
                field_nr: str = identify_mapping_field_nr(thesaurus_subfield_1)
                field_6xx: Field = map_thesaurus_on_marc_6xx(marc_thesaurus_field, field_nr)
                record.add_field(field_6xx)
                logger.debug("Field No. %s: %s", thesaurus_field_counter, field_6xx)
            except ValueError:
                logger.error("Field No. %s: No unique mapping for notation %s\n"
                             "(Thesaurus is mapped on field 600 and 651)",
                             thesaurus_field_counter, thesaurus_subfield_1)
                is_record_format_error = True
                record_error_no += 1

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
