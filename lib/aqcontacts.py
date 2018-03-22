import logging
import sys
import os

import lib.database_connections.mariadb as mariadb
import lib.database_connections.oracle as oracle
import lib.oracle_helper.z70 as z70_helper
import lib.oracle_helper.z72 as z72_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/113000_aqcontacts_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/aqcontacts_data_import.sql'

GENERIC_MAIN_CONTACT_NAME = 'Main contact'
GENERIC_ORDER_CONTACT_NAME = 'Order contact'
GENERIC_CLAIM_CONTACT_NAME = 'Claim contact'
GENERIC_PAYMENT_CONTACT_NAME = 'Payment contact'
GENERIC_RETURNS_CONTACT_NAME = 'Returns contact'


def map_boolean_to_0_or_1(boolean_value):
    if boolean_value:
        return 1
    else:
        return 0


def create_name_from_type(address_type):
    if address_type == 1:
        return GENERIC_ORDER_CONTACT_NAME
    elif address_type == 2:
        return GENERIC_CLAIM_CONTACT_NAME
    elif address_type == 3:
        return GENERIC_PAYMENT_CONTACT_NAME
    elif address_type == 4:
        return GENERIC_RETURNS_CONTACT_NAME
    else:
        return None


def process_z72_result(previous_results, query_result):
    updated_results = previous_results.copy()

    [vendor_key, address_type] = z72_helper.split_rec_key(query_result[0])
    if int(address_type) < 1 or int(address_type) > 4:
        return previous_results

    aqbookseller_data = mariadb.get_aqbookseller_by_aleph_vendor_key(vendor_key)

    aqcontacts_data = {
        'phone': query_result[3],
        'email': query_result[5],
        'notes': query_result[11],
    }

    z70_data = oracle.get_z70_by_rec_key(vendor_key.ljust(25))

    if z70_data.rowcount > 1:
        logger.error('Found more than one dataset in Z70 for vendor key ' + vendor_key)

    parsed_z70_data = z70_helper.parse_contact_fields(z70_data)

    if 'name' in parsed_z70_data:
        aqcontacts_data['name'] = parsed_z70_data['name']

    if 'email' in parsed_z70_data and aqcontacts_data['email'] is None:
        aqcontacts_data['email'] = parsed_z70_data['email']

    if 'email' in parsed_z70_data and aqcontacts_data['email'] is not None:

        if parsed_z70_data['email'] != aqcontacts_data['email'].strip():
            logger.warning('Email provided in both z70 and z72, keeping value from z72.')
            logger.warning(' z70: ' + parsed_z70_data['email'])
            logger.warning(' z72: ' + aqcontacts_data['email'])
            logger.warning(' Writing z70 variant to "notes".')
            if aqcontacts_data['notes'] is None:
                aqcontacts_data['notes'] = ''

    if 'notes' in parsed_z70_data:
        if aqcontacts_data['notes'] is None:
            aqcontacts_data['notes'] = ''
        aqcontacts_data['notes'] += ', ' + parsed_z70_data['notes']

    if all(value is None for value in aqcontacts_data.values()):
        return previous_results

    if aqcontacts_data['notes'] is not None:
        aqcontacts_data['notes'] = aqcontacts_data['notes'].replace('\"', '\'')

    if 'name' not in aqcontacts_data:
        aqcontacts_data['name'] = create_name_from_type(int(address_type))

    aqcontacts_data['name'] = aqcontacts_data['name'].replace('\"', '\'')

    aqcontacts_data['orderacquisition'] = map_boolean_to_0_or_1(int(address_type) == 1)
    aqcontacts_data['claimacquisition'] = map_boolean_to_0_or_1(int(address_type) == 2)
    aqcontacts_data['claimissues'] = map_boolean_to_0_or_1(int(address_type) == 2)
    aqcontacts_data['acqprimary'] = 0
    aqcontacts_data['serialsprimary'] = 0
    aqcontacts_data['booksellerid'] = aqbookseller_data[0]

    if vendor_key not in previous_results:
        updated_results[vendor_key] = []

    updated_results[vendor_key].append(aqcontacts_data)

    return updated_results


def fetch_data(credentials):
    oracle.establish_connection(credentials)
    mariadb.establish_connection()

    z72_result = dict()
    cur = oracle.get_z72()
    for query_result in cur:
        z72_result = process_z72_result(z72_result, query_result)

    cur.close()
    oracle.close_connection()

    return z72_result


def merge_with_same_name(contact_list):
    index = 0
    updated_contact_list = []
    while index < len(contact_list):
        if len(updated_contact_list) == 0:
            updated_contact_list.append(contact_list[index])
        else:
            for key in contact_list[index]:
                value = contact_list[index][key]
                previous_contact_data = updated_contact_list[-1]
                if (key not in previous_contact_data
                        or previous_contact_data[key] is None
                        or previous_contact_data[key] == 0):
                    previous_contact_data[key] = value
                if (previous_contact_data[key] is not None
                        and value is not None
                        and not (value == 0 and previous_contact_data[key] == 1)
                        and previous_contact_data[key] != value):

                    if not (previous_contact_data[key] in value or value in previous_contact_data[key]):
                        logger.debug('Unhandled case: 2 contacts with same name have each a different value set for')
                        logger.debug(' key: ' + str(key))
                        logger.debug(' Name: ' + previous_contact_data['name'])
                        logger.debug(' First contact value: ' + str(value))
                        logger.debug(' Second contact value: ' + str(previous_contact_data[key]))
                        logger.debug(' Writing second variant to "notes" of the first one.')

                        if previous_contact_data['notes'] is None:
                            previous_contact_data['notes'] = ''

                        previous_contact_data['notes'] += ", " + value

        index += 1

    # Sanity check: Only one item should remain:
    if len(updated_contact_list) != 1:
        logger.error('More than one contact after merge:')
        logger.error(updated_contact_list)
    else:
        return updated_contact_list[0]


def merge_with_generic_names(contact_list):
    merged_list = []
    result = contact_list[0]
    result['name'] = GENERIC_MAIN_CONTACT_NAME
    index = 1
    while index < len(contact_list):
        contact = contact_list[index]
        keep_updated_result = True
        updated_result = result
        for key in contact.keys():
            if key == 'name':
                continue
            if contact[key] != updated_result[key]:
                if contact[key] is None:
                    continue
                if updated_result[key] is None:
                    updated_result[key] = contact[key]
                    continue
                if key in ['orderacquisition', 'claimacquisition', 'claimissues']:
                    updated_result[key] = 1
                    continue
                if key == 'notes':
                    updated_result[key] += ', ' + contact[key]
                    continue

                logger.debug('Different values for key: %s' % key)
                logger.debug(contact[key])
                logger.debug(result[key])
                logger.debug('Keeping generic contact: ')
                logger.debug(contact)

                merged_list.append(contact)
                keep_updated_result = False
                break

        if keep_updated_result:
            result = updated_result

        index += 1

    merged_list.append(result)
    return merged_list


def merge_duplicates(results):

    updated_results = {}

    for vendor_key in results:

        contact_list = results[vendor_key]

        if len(contact_list) == 1:
            updated_results[vendor_key] = contact_list
            continue

        dict_by_name = dict()
        generic_name_list = []

        for contact in contact_list:

            if contact['name'] in [GENERIC_ORDER_CONTACT_NAME,
                                   GENERIC_CLAIM_CONTACT_NAME,
                                   GENERIC_PAYMENT_CONTACT_NAME,
                                   GENERIC_RETURNS_CONTACT_NAME]:
                generic_name_list.append(contact)
                continue

            if contact['name'] not in dict_by_name:
                dict_by_name[contact['name']] = []
            dict_by_name[contact['name']].append(contact)

        updated_contact_list = []

        for key in dict_by_name.keys():
            # If the name only occurs once, it is accepted.
            if len(dict_by_name[key]) == 1:
                updated_contact_list.append(dict_by_name[key])
            # Otherwise, we try to merge the entries into one.
            else:
                updated_contact_list.append(merge_with_same_name(dict_by_name[key]))

        if len(generic_name_list) > 0:
            updated_contact_list.extend(merge_with_generic_names(generic_name_list))

        updated_results[vendor_key] = updated_contact_list
    return updated_results


def generate_insert_statements(data_list):

    database_columns = [
        'name', 'position', 'phone', 'altphone', 'fax', 'email', 'notes', 'orderacquisition', 'claimacquisition',
        'claimissues', 'acqprimary', 'serialsprimary', 'booksellerid'
    ]

    mapping_table_statement = import_table_statement = 'INSERT INTO aqcontacts ('
    keys_len = len(database_columns)

    for idx, key in enumerate(database_columns):

        if idx == keys_len - 1:

            import_table_statement += key

            mapping_table_statement += key
            mapping_table_statement += ', ALEPH_VENDOR_CODE'
        else:
            import_table_statement += key + ','
            mapping_table_statement += key + ','

    import_table_statement += ')\nVALUES'
    mapping_table_statement += ')\nVALUES'

    counter = 0

    for aleph_key in data_list:
        contacts = data_list[aleph_key]
        for contact in contacts:
            if counter != 0:
                import_table_statement += ','
                mapping_table_statement += ','

            import_table_statement += '\n('
            mapping_table_statement += '\n('

            for idx, key in enumerate(database_columns):
                if idx == keys_len - 1:

                    if key in contact and contact[key] is not None:
                        import_table_statement += '"' + str(contact[key]) + '"'
                        mapping_table_statement += '"' + str(contact[key]) + '"'
                    else:
                        import_table_statement += 'NULL'
                        mapping_table_statement += 'NULL'

                    mapping_table_statement += ', "' + aleph_key + '"'
                else:

                    if key in contact and contact[key] is not None:
                        import_table_statement += '"' + str(contact[key]) + '",'
                        mapping_table_statement += '"' + str(contact[key]) + '",'
                    else:
                        import_table_statement += 'NULL,'
                        mapping_table_statement += 'NULL,'

            import_table_statement += ')'
            mapping_table_statement += ')'

            counter = counter + 1

    import_table_statement += ';\n'
    mapping_table_statement += ';\n'

    return [import_table_statement, mapping_table_statement]


def write_data(data):
    logger.info('Writing data to file and mapping database.')

    mariadb.establish_connection()

    cursor = mariadb.get_cursor()
    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")

        statements = generate_insert_statements(data)

        import_file.write(statements[0])
        mapping_file.write(statements[1])

        cursor.execute(statements[1])

    mariadb.commit()


def start(oracle_credentials):
    results = fetch_data(oracle_credentials)
    filtered_results = merge_duplicates(results)
    write_data(filtered_results)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
