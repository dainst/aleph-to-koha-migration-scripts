import logging
import sys
import os
import re
import pickle

import lib.database_connections.oracle as oracle
import lib.mappings.library_keys as library_keys
import lib.mappings.marc_mappings as marc_mapping
import lib.oracle_helper.dates as date_helper
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.z00 as z00_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/' \
                                       '043000_subscription_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/subscription_data_import.sql'

SUBSCRIPTION_COUNTER = 1
FREQUENCY_MAPPING = None
PATTERN_MAPPING = None
SYS_NUMBER_TO_BIB_ID_MAPPING_PATH = script_dir + '/../pickles/SYS_NUMBER_TO_BIB_ID_MAPPING.pickle'
SYS_NUMBER_TO_BIB_ID_MAPPING = None
Z00_TO_BIBLIOGRAPHIC_ID_MAPPING = dict()
Z08_DATA = dict()

'''
  `cost` int(11) DEFAULT '0',
  `weeklength` int(11) DEFAULT '0',
  `monthlength` int(11) DEFAULT '0',
  `numberlength` int(11) DEFAULT '0',
  `notes` mediumtext COLLATE utf8_unicode_ci,
  `lastvalue1` int(11) DEFAULT NULL,
  `innerloop1` int(11) DEFAULT '0',
  `lastvalue2` int(11) DEFAULT NULL,
  `innerloop2` int(11) DEFAULT '0',
  `lastvalue3` int(11) DEFAULT NULL,
  `innerloop3` int(11) DEFAULT '0',
  `irregularity` text COLLATE utf8_unicode_ci,
  `skip_serialseq` tinyint(1) NOT NULL DEFAULT '0',
  `letter` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `locale` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
  `distributedto` text COLLATE utf8_unicode_ci,
  `callnumber` text COLLATE utf8_unicode_ci,
  `reneweddate` date DEFAULT NULL,
'''


def parse_z16(parsed_results, data):
    global SUBSCRIPTION_COUNTER
    global FREQUENCY_MAPPING
    global PATTERN_MAPPING
    global Z00_TO_BIBLIOGRAPHIC_ID_MAPPING
    global SYS_NUMBER_TO_BIB_ID_MAPPING

    result = dict()
    doc_key = data[0][0:9]

    budget = mariadb.get_budget_by_code(data[-2][0:50])

    if budget is None:
        logger.warning('No found for Aleph code "%s". Subscription (Z16): %s' % (data[-2][0:50], data[0]))
    else:
        result['aqbudgetid'] = budget[0]

    try:
        sys_number = Z00_TO_BIBLIOGRAPHIC_ID_MAPPING[doc_key]
        koha_bib_id = SYS_NUMBER_TO_BIB_ID_MAPPING[sys_number]
    except KeyError:
        logger.warning('Koha bibliographic ID missing for subscription (Z16): %s.' % data[0])
        return parsed_results

    result['biblionumber'] = koha_bib_id
    result['branchcode'] = library_keys.map_aleph_key(data[2].strip())
    result['startdate'] = date_helper.process_aleph_date(data[3])  # TODO: Check if this is a valid interpretation
    result['firstacquidate'] = date_helper.process_aleph_date(data[3])  # ^---

    result['itemtype'] = 'CR'
    result['internalnotes'] = data[24]
    result['status'] = 1  # status == 1 means "expected"
    result['countissuesperunit'] = 1
    result['serialsadditems'] = 0  # does receiving this serial create an item record
    result['manualhistory'] = 0  # yes or no to managing the history manually
    result['skip_serialseq'] = 0
    result['graceperiod'] = 0
    result['closed'] = 0

    if data[4] == '20991231':
        end_date = None
    else:
        end_date = date_helper.process_aleph_date(data[4])
    result['enddate'] = end_date

    result['location'] = marc_mapping.map_shelving_location(data[13], koha_bib_id)

    if doc_key in PATTERN_MAPPING:
        result['numberpattern'] = PATTERN_MAPPING[doc_key]['id']
    else:
        logger.warning('No number pattern for Aleph subscription (Z16): %s.' % data[0])

    if doc_key in FREQUENCY_MAPPING:
        frequency_list = FREQUENCY_MAPPING[doc_key]
        if len(frequency_list) == 1:
            result['periodicity'] = frequency_list[0][0]
        else:
            [issue_frequency] = [frequency[0:2] for frequency in frequency_list if frequency[2] == 'issue']
            result['periodicity'] = issue_frequency[0]
    else:
        logger.warning('No periodicity information for Aleph subscription (Z16): %s.' % data[0])

    bookseller = mariadb.get_aqbookseller_by_aleph_vendor_key(data[5])
    if bookseller is None:
        logger.warning('No bookseller found for Aleph vendor code "%s". Aleph subscription (Z16): %s.'
                       % (data[5], data[0]))
    else:
        result['aqbooksellerid'] = bookseller[0]

    result['subscriptionid'] = SUBSCRIPTION_COUNTER
    SUBSCRIPTION_COUNTER += 1

    parsed_results[data[0]] = result

    return parsed_results


def fetch_data(credentials):
    global FREQUENCY_MAPPING
    global PATTERN_MAPPING
    global Z00_TO_BIBLIOGRAPHIC_ID_MAPPING

    with open(script_dir + '/../pickles/subscription_frequencies_mapping.pickle', 'rb') as mapping_file:
        FREQUENCY_MAPPING = pickle.load(mapping_file)
    with open(script_dir + '/../pickles/subscription_patterns_mapping.pickle', 'rb') as mapping_file:
        PATTERN_MAPPING = pickle.load(mapping_file)

    oracle.establish_connection(credentials)
    mariadb.establish_connection()

    logger.info('Fetching title IDs...')
    data_cursor = oracle.get_z00_data()
    for query_result in data_cursor:
        bibliographic_id = z00_helper.get_bibliographic_id_for_adm_number(query_result)
        if bibliographic_id is not None:
            Z00_TO_BIBLIOGRAPHIC_ID_MAPPING[query_result[0]] = bibliographic_id
    data_cursor.close()
    logger.info('Done.')

    cursor = oracle.get_subscription_data()
    subscriptions = dict()
    for row in cursor:
        subscriptions = parse_z16(subscriptions, row)
    cursor.close()

    subscription_to_order_mapping = dict()
    data_cursor = oracle.get_subscription_to_order_mapping()
    for query_result in data_cursor:
        subscription_to_order_mapping[query_result[0]] = query_result[1]

    with open(script_dir + '/../pickles/subscription_to_order_mapping.pickle', 'wb') as mapping_file:
        pickle.dump(subscription_to_order_mapping, mapping_file)

    return subscriptions


def generate_insert_statements(data_dict, database_columns):
    import_table_statement = 'INSERT INTO subscription ('
    keys_len = len(database_columns)

    for idx, key in enumerate(database_columns):

        if idx == keys_len - 1:
            import_table_statement += key
        else:
            import_table_statement += key + ','

    import_table_statement += ')\nVALUES'

    counter = 0

    for aleph_key in data_dict:
        subscription = data_dict[aleph_key]
        if counter != 0:
            import_table_statement += ','

        import_table_statement += '\n('

        for idx, key in enumerate(database_columns):
            if idx == keys_len - 1:
                if key in subscription and subscription[key] is not None:
                    import_table_statement += '"' + str(subscription[key]) + '"'
                else:
                    import_table_statement += 'NULL'
            else:
                if key in subscription and subscription[key] is not None:
                    import_table_statement += '"' + str(subscription[key]) + '",'
                else:
                    import_table_statement += 'NULL,'

        import_table_statement += ')'
        counter = counter + 1

    import_table_statement += ';\n'

    return import_table_statement


def write_data(result_dict):

    database_columns = ['biblionumber', 'subscriptionid', 'librarian', 'startdate', 'aqbooksellerid', 'cost',
                        'weeklength', 'monthlength', 'numberlength', 'periodicity', 'countissuesperunit',  'status',
                        'lastvalue1', 'innerloop1', 'lastvalue2', 'innerloop2', 'lastvalue3', 'innerloop3',
                        'firstacquidate', 'manualhistory', 'irregularity', 'skip_serialseq', 'letter', 'numberpattern',
                        'locale', 'distributedto', 'internalnotes', 'callnumber', 'location', 'branchcode',
                        'lastbranch', 'serialsadditems', 'staffdisplaycount', 'opacdisplaycount', 'graceperiod',
                        'enddate', 'closed', 'reneweddate', 'itemtype', 'previousitemtype']

    with open(IMPORT_SQL_OUTPUT_PATH, 'w') as import_file, open(MAPPING_SQL_OUTPUT_PATH, 'w') as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        import_table_statement = \
            generate_insert_statements(result_dict, database_columns)

        import_file.write(import_table_statement)
        mapping_file.write(import_table_statement)
        cursor.execute(import_table_statement)

        mariadb.commit()
        cursor.close()


def start(credentials):
    global SYS_NUMBER_TO_BIB_ID_MAPPING_PATH
    global SYS_NUMBER_TO_BIB_ID_MAPPING

    with open(SYS_NUMBER_TO_BIB_ID_MAPPING_PATH, 'rb') as id_mapping_file:
        SYS_NUMBER_TO_BIB_ID_MAPPING = pickle.load(id_mapping_file)

    subscriptions = fetch_data(credentials)
    write_data(subscriptions)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
