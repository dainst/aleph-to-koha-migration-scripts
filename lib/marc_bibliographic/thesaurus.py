from pymarc import Field

import logging

THESAURUS_FIELD_CODE = '999'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def map_thesaurus_on_marc_65x(record):
    marc_thesaurus_fields = record.get_fields(THESAURUS_FIELD_CODE)
    thesaurus_field_count = len(marc_thesaurus_fields)
    logger.info("%s thesaurus field(s) found.", thesaurus_field_count)

    thesaurus_field_counter = 1
    for marc_thesaurus_field in marc_thesaurus_fields:
        logger.debug("Field No. %s: %s", thesaurus_field_counter, marc_thesaurus_field)
        thesaurus_subfield_a = marc_thesaurus_field['a']
        thesaurus_subfield_e = marc_thesaurus_field['e']
        thesaurus_subfield_m = marc_thesaurus_field['m']
        thesaurus_subfield_r = marc_thesaurus_field['r']
        thesaurus_subfield_1 = marc_thesaurus_field['1']
        field_651 = None

        if thesaurus_subfield_a is not None or thesaurus_subfield_e is not None or thesaurus_subfield_m is not None or \
                thesaurus_subfield_r is not None or thesaurus_subfield_1 is not None:

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

            if thesaurus_subfield_1 is not None:
                field_651.add_subfield('2', thesaurus_subfield_1)

            record.add_field(field_651)

        logger.debug("Field No. %s: %s", thesaurus_field_counter, field_651)
        thesaurus_field_counter += 1


def prepare_marc(record):
    logger.info("Processing thesaurus information of Marc record: '%s' ...", record.leader)

    map_thesaurus_on_marc_65x(record)
    record.remove_fields(THESAURUS_FIELD_CODE)

    logger.info("Marc Record '%s' process completed!\n", record.leader)
