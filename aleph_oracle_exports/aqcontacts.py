import logging
import sys

import database_connections.mariadb as mariadb
import database_connections.oracle as oracle
import oracle_helper.z70 as z70_helper
import oracle_helper.z72 as z72_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

MAPPING_SQL_OUTPUT_PATH = './aleph_oracle_exports/mariadb_intermediate_values/00200_aqcontacts_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = './aleph_oracle_exports/ready_for_import/aqcontacts_data_import.sql'


def map_boolean_to_0_or_1(boolean_value):
    if boolean_value:
        return 1
    else:
        return 0


def create_name_from_type(address_type):
    if address_type == 1:
        return 'Vendor contact'
    elif address_type == 2:
        return 'Claim contact'
    elif address_type == 3:
        return 'Claim contact'
    elif address_type == 4:
        return 'Claim contact'
    else:
        return None


def process_z72_result(previous_results, query_result):
    updated_results = previous_results.copy()

    [vendor_key, address_type] = z72_helper.split_rec_key(query_result[0])
    if int(address_type) < 1 or int(address_type) > 4:
        return previous_results

    aqbookseller_data = mariadb.get_aqbookseller_by_aleph_key(vendor_key)

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

    if 'name' not in aqcontacts_data:
        aqcontacts_data['name'] = create_name_from_type(int(address_type))

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


def generate_insert_statement(aleph_key, data, produce_mapping_table):
    statement = 'INSERT INTO aqcontacts ('
    keys = data.keys()
    keys_len = len(data)
    for idx, key in enumerate(keys):

        if data[key] is None:
            continue

        if idx == keys_len - 1:
            statement += key

            if produce_mapping_table:
                statement += ', ALEPH_VENDOR_KEY'
        else:
            statement += key + ','

    statement += ') VALUES('

    for idx, key in enumerate(keys):

        if data[key] is None:
            continue

        if idx == keys_len - 1:
            statement += '"' + str(data[key]) + '"'
            if produce_mapping_table:
                statement += ', "' + str(aleph_key) + '"'
        else:
            statement += '"' + str(data[key]) + '",'

    statement += ')'
    statement += ';\n'

    return statement


def conflate_duplicates(results):

    updated_results = {}

    for vendor_key in results:

        contact_list = sorted(results[vendor_key], key=lambda k: k['name'])

        updated_contact_list = []

        index = 0

        while index < len(contact_list):
            if len(updated_contact_list) == 0 or updated_contact_list[-1]['name'] != contact_list[index]['name']:
                updated_contact_list.append(contact_list[index])
            else:
                for key in contact_list[index]:
                    value = contact_list[index][key]
                    if (key not in updated_contact_list[-1]
                            or updated_contact_list[-1][key] is None
                            or updated_contact_list[-1][key] == 0):
                        updated_contact_list[-1][key] = value
                    if (updated_contact_list[-1][key] is not None
                            and value is not None
                            and not (value == 0 and updated_contact_list[-1][key] == 1)
                            and updated_contact_list[-1][key] != value):
                        logger.warning('Unhandled case: 2 contacts with same name have each a different value set for')
                        logger.warning(' key: ' + str(key))
                        logger.warning(' Name: ' + updated_contact_list[-1]['name'])
                        logger.warning(' First contact value: ' + str(value))
                        logger.warning(' Second contact value: ' + str(updated_contact_list[-1][key]))
                        logger.warning(' Writing second variant to "notes".')

                        if updated_contact_list[-1]['notes'] is None:
                            updated_contact_list[-1]['notes'] = ''

                        updated_contact_list[-1]['notes'] += ", " + value

            index += 1

        updated_results[vendor_key] = updated_contact_list
    return updated_results


def write_data(data):
    logger.info('Writing data to file and mapping database.')

    mariadb.establish_connection()

    cursor = mariadb.get_cursor()
    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ';')

        for aleph_key in data.keys():

            for contact in data[aleph_key]:

                import_file.write(generate_insert_statement(aleph_key, contact, False))

                mapping_statement = generate_insert_statement(aleph_key, contact, True)

                mapping_file.write(mapping_statement)
                cursor.execute(mapping_statement)

    mariadb.commit()


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    results = fetch_data(sys.argv[1])
    filtered_results = conflate_duplicates(results)
    write_data(filtered_results)

