from pymarc import Field

import logging

THESAURUS_FIELD_CODE = '999'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def map_999_2_65x(record):
    marc_thesaurus_fields = record.get_fields(THESAURUS_FIELD_CODE)
    thesaurus_field_count = len(marc_thesaurus_fields)
    logger.info("%s thesaurus field(s) found.", thesaurus_field_count)

    thesaurus_field_counter = 1
    for marc_thesaurus_field in marc_thesaurus_fields:
        logger.debug("Field No. %s: %s", thesaurus_field_counter, marc_thesaurus_field)
        thesaurus_subfield_a = marc_thesaurus_field['a']
        thesaurus_subfield_r = marc_thesaurus_field['r']
        thesaurus_subfield_1 = marc_thesaurus_field['1']
        thesaurus_subfield_9 = marc_thesaurus_field['9']
        field_651 = None

        if thesaurus_subfield_a is not None:
            if thesaurus_subfield_r is not None:
                field_651 = Field(tag='651', indicators=['#', '#'], subfields=['g', thesaurus_subfield_a])
            else:
                field_651 = Field(tag='651', indicators=['#', '#'], subfields=['a', thesaurus_subfield_a])
            record.add_field(field_651)

        if thesaurus_subfield_r is not None:
            field_651 = Field(tag='651', indicators=['#', '#'], subfields=['a', thesaurus_subfield_r])
            record.add_field(field_651)

        if thesaurus_subfield_1 is not None:
            field_651 = Field(tag='651', indicators=['#', '#'], subfields=['2', thesaurus_subfield_1])
            record.add_field(field_651)

        if thesaurus_subfield_9 is not None:
            pass

        logger.debug("Field No. %s: %s", thesaurus_field_counter, field_651)
        thesaurus_field_counter += 1


def prepare_marc(record):
    record_error_no = 0
    is_record_format_error = False
    is_record_format_warning = False
    is_record_format_info = False
    is_record_format_debugging = False

    logger.info("Processing thesaurus information of Marc record: '%s' ...", record.leader)

    map_999_2_65x(record)

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
