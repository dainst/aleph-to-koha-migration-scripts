import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def split_rec_key(rec_key):
    return [rec_key[0:-5].strip(), rec_key[-5].strip()]


def parse_contact_fields(z70_data):

    result = {}

    for z70_query_result in z70_data:
        # Skip ROM for now.
        if z70_query_result[0].startswith('R/'):
            return result
        else:
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
                        result['email'] = value.strip()
                    elif len(value.strip()) > 40:
                        logger.debug('Unable to decide what this is, string is too long, skipping:')
                        logger.debug(value)
                        logger.debug('VENDOR_KEY: ' + z70_query_result[0])
                        continue
                    elif len(value) < 4:
                        logger.debug('Unable to decide what this is, string is too short, skipping:')
                        logger.debug(value)
                        logger.debug('VENDOR_KEY: ' + z70_query_result[0])
                        continue
                    else:
                        result['name'] = value.strip()

    return result
