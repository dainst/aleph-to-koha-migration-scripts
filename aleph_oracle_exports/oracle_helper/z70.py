import logging

import re

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

EXTRACT_EMAIL_REGEX = re.compile(r'([A-Za-z0-9]+@.+\.\w+)\s?.*', re.IGNORECASE)


def split_rec_key(rec_key):
    return [rec_key[0:-5].strip(), rec_key[-5].strip()]


def parse_contact_fields(z70_data):

    result = {}

    for z70_query_result in z70_data:
        z70_contact_fields = z70_query_result[8:12]

        if all(value is None for value in z70_contact_fields):
            continue
        else:
            for value in z70_contact_fields:
                if value is None:
                    continue
                elif ('IBAN' in value) or ('BIC' in value) or ('BLZ' in value):
                    result['bank_account'] = value.strip()
                elif '@' in value:
                    match = re.search(EXTRACT_EMAIL_REGEX, value)
                    if match:
                        result['email'] = match.group(1)

                        if match.group(0) != match.group(1):
                            logger.warning('Value contains data besides email adress:' + match.group(1))
                            logger.warning(' ' + value)
                            logger.warning(' Writing rest in "notes".')

                            rest = match.group(0).replace(match.group(1), '')
                            if 'notes' not in result:
                                result['notes'] = ''
                            result['notes'] += ', ' + rest
                elif len(value.strip()) > 20:
                    logger.warning('Unable to decide what this is, string is too long:')
                    logger.warning(value)
                    logger.warning(' VENDOR_KEY: ' + z70_query_result[0])
                    logger.warning(' Writing to "notes".')

                    if 'notes' not in result:
                        result['notes'] = ''
                    result['notes'] += ', ' + value
                elif len(value) < 4:
                    logger.warning('Unable to decide what this is, string is too short:')
                    logger.warning(value)
                    logger.warning(' VENDOR_KEY: ' + z70_query_result[0])
                    logger.warning(' Writing to "notes".')

                    if 'notes' not in result:
                        result['notes'] = ''
                    result['notes'] += ', ' + value
                else:
                    result['name'] = value.strip()

    return result
