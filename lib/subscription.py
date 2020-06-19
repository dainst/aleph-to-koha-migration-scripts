import logging
import sys
import os
import pickle

import lib.database_connections.oracle as oracle
import lib.mappings.library_keys as library_keys
import lib.mappings.marc_mappings as marc_mapping
import lib.oracle_helper.dates as date_helper
import lib.database_connections.mariadb as mariadb
import lib.mappings.fallback_budgets as fallback_budgets

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
order_to_budget_mapping = dict()
SUBSCRIPTION_TO_ZENON_ID_MAPPING = dict()
ORDER_TO_SUBSCRIPTION_MAPPING = dict()
Z08_DATA = dict()

missing_budget = []

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


def parse_z16(parsed_results, data, subscriptionhistory_results):
    global SUBSCRIPTION_COUNTER
    global FREQUENCY_MAPPING
    global PATTERN_MAPPING
    global SUBSCRIPTION_TO_ZENON_ID_MAPPING
    global SYS_NUMBER_TO_BIB_ID_MAPPING
    global order_to_budget_mapping
    global ORDER_TO_SUBSCRIPTION_MAPPING
    global missing_budget

    subscription_result = dict()
    subscriptionhistory_result = dict()
    doc_key = data[0][0:-3]

    try:
        budget = mariadb.get_budget_by_code(order_to_budget_mapping[data[-1]][0:50])
        if budget is not None:
            subscription_result['aqbudgetid'] = budget[0]
    except KeyError as e:
        subscription_result['aqbudgetid'] = mariadb.get_budget_by_code(
            fallback_budgets.get_budget_for_method_of_acquisition(data[-2].strip())
        )[0]
        missing_budget.append((doc_key, data[-1]))
    try:
        sys_number = SUBSCRIPTION_TO_ZENON_ID_MAPPING[data[0]]
        try:
            koha_bib_id = SYS_NUMBER_TO_BIB_ID_MAPPING[sys_number]
        except KeyError:
            logger.error(f'Koha bibliographic ID missing system number {sys_number}, linked to'
                         f' subscription (Z16): {data[0]}.')
            return parsed_results, subscriptionhistory_results
    except KeyError:
        logger.error(f'Unable map subscription {doc_key} to system number.')
        return parsed_results, subscriptionhistory_results

    subscription_result['biblionumber'] = koha_bib_id
    subscriptionhistory_result['biblionumber'] = subscription_result['biblionumber']
    subscription_result['branchcode'] = library_keys.map_aleph_key(data[2].strip())
    subscription_result['startdate'] = date_helper.process_aleph_date(data[3])  # TODO: Check if this is a valid interpretation
    subscriptionhistory_result['histstartdate'] = subscription_result['startdate']
    subscription_result['firstacquidate'] = date_helper.process_aleph_date(data[3])  # ^---

    subscription_result['itemtype'] = 'CR'
    subscription_result['internalnotes'] = data[24]
    subscription_result['status'] = 1  # status == 1 means "expected"
    subscription_result['countissuesperunit'] = 1
    subscription_result['serialsadditems'] = 0  # does receiving this serial create an item record
    subscription_result['manualhistory'] = 1  # yes or no to managing the history manually
    subscription_result['skip_serialseq'] = 0
    subscription_result['graceperiod'] = 0
    subscription_result['closed'] = 0

    if data[4] == 20991231:
        end_date = None
    else:
        end_date = date_helper.process_aleph_date(data[4])
    subscription_result['enddate'] = end_date

    if data[13] is not None:
        subscription_result['location'] = marc_mapping.map_shelving_location(data[13].strip(), subscription_result['branchcode'])
    else:
        subscription_result['location'] = marc_mapping.map_shelving_location(None, subscription_result['branchcode'])

    if doc_key[0:9] in PATTERN_MAPPING:
        subscription_result['numberpattern'] = PATTERN_MAPPING[doc_key[0:9]]['id']
    else:
        logger.warning('No number pattern for Aleph subscription (Z16): %s.' % data[0])

    if doc_key[0:9] in FREQUENCY_MAPPING:
        frequency_list = FREQUENCY_MAPPING[doc_key[0:9]]
        if len(frequency_list) == 1:
            subscription_result['periodicity'] = frequency_list[0][0]
        else:
            [issue_frequency] = [frequency[0:2] for frequency in frequency_list if frequency[2] == 'issue']
            subscription_result['periodicity'] = issue_frequency[0]
    else:
        logger.warning('No periodicity information for Aleph subscription (Z16): %s.' % data[0])

    bookseller = mariadb.get_aqbookseller_by_aleph_vendor_key(data[5])
    if bookseller is None:
        logger.warning('No bookseller found for Aleph vendor code "%s". Aleph subscription (Z16): %s.'
                       % (data[5], data[0]))
    else:
        subscription_result['aqbooksellerid'] = bookseller[0]

    subscriptionhistory_result['missinglist'] = ""
    subscriptionhistory_result['recievedlist'] = ""

    subscription_result['subscriptionid'] = SUBSCRIPTION_COUNTER
    subscriptionhistory_result['subscriptionid'] = SUBSCRIPTION_COUNTER
    ORDER_TO_SUBSCRIPTION_MAPPING[data[-1]] = subscription_result

    SUBSCRIPTION_COUNTER += 1

    if data[0] in parsed_results:
        parsed_results[data[0]] += subscription_result
    else:
        parsed_results[data[0]] = [subscription_result]

    if data[0] in subscriptionhistory_results:
        subscriptionhistory_results[data[0]] += subscriptionhistory_result
    else:
        subscriptionhistory_results[data[0]] = [subscriptionhistory_result]

    return parsed_results, subscriptionhistory_results


def fetch_data(credentials):
    global FREQUENCY_MAPPING
    global PATTERN_MAPPING
    global SUBSCRIPTION_TO_ZENON_ID_MAPPING
    global order_to_budget_mapping

    with open(script_dir + '/../pickles/subscription_frequencies_mapping.pickle', 'rb') as mapping_file:
        FREQUENCY_MAPPING = pickle.load(mapping_file)
    with open(script_dir + '/../pickles/subscription_patterns_mapping.pickle', 'rb') as mapping_file:
        PATTERN_MAPPING = pickle.load(mapping_file)

    oracle.establish_connection(credentials)
    mariadb.establish_connection()

    logger.info('Fetching title IDs...')
    data_cursor = oracle.get_subscription_to_zenon_id_pairs()
    for query_result in data_cursor:
        SUBSCRIPTION_TO_ZENON_ID_MAPPING[query_result[0]] = query_result[1]
    data_cursor.close()
    logger.info('Done.')

    logger.info('Fetching budget data...')
    data_cursor = oracle.get_orders_to_budgets_mapping()
    for query_result in data_cursor:
        if query_result[0] in order_to_budget_mapping:
            logger.warning('Order already mapped to budget: ')
            logger.warning(f'{query_result[0]}: {order_to_budget_mapping[query_result[0]]}')
            logger.warning('New value:')
            logger.warning(f'{query_result[0]}: {query_result[1].strip()}')
        order_to_budget_mapping[query_result[0]] = query_result[1].strip()
    data_cursor.close()

    data_cursor = oracle.get_orders_to_budgets_mapping_variant()
    for query_result in data_cursor:
        if query_result[0] not in order_to_budget_mapping:
            order_to_budget_mapping[query_result[0]] = query_result[1].strip()
    data_cursor.close()
    logger.info('Done.')

    cursor = oracle.get_subscription_data()
    subscriptions = dict()
    subscriptionhistories = dict()
    for row in cursor:
        (subscriptions, subscriptionhistories) = parse_z16(
            subscriptions, row, subscriptionhistories
        )
    cursor.close()

    with open(script_dir + '/../pickles/order_to_subscription_mapping.pickle', 'wb') as mapping_file:
        pickle.dump(ORDER_TO_SUBSCRIPTION_MAPPING, mapping_file)

    return subscriptions, subscriptionhistories


def generate_insert_statements(data_dict, db_table, database_columns):
    import_table_statement = 'INSERT INTO ' + db_table + ' ('
    keys_len = len(database_columns)

    for idx, key in enumerate(database_columns):

        if idx == keys_len - 1:
            import_table_statement += key
        else:
            import_table_statement += key + ','

    import_table_statement += ')\nVALUES'

    counter = 0

    for aleph_key in data_dict:
        subscriptions = data_dict[aleph_key]
        for subscription in subscriptions:
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


def write_data(result_dict, db_table, columns):

    if db_table == 'subscription':
        flag = 'w'
    else:
        flag = 'a'

    with open(IMPORT_SQL_OUTPUT_PATH, flag) as import_file, open(MAPPING_SQL_OUTPUT_PATH, flag) as mapping_file:

        mapping_file.write('USE ' + mariadb.get_db_name() + ";\n\n")
        mariadb.establish_connection()

        cursor = mariadb.get_cursor()

        import_table_statement = \
            generate_insert_statements(result_dict, db_table, columns)

        import_file.write(import_table_statement)
        mapping_file.write(import_table_statement)
        cursor.execute(import_table_statement)

        mariadb.commit()
        cursor.close()


def start(credentials, sys_number_to_bib_number_mapping):
    global SYS_NUMBER_TO_BIB_ID_MAPPING_PATH
    global SYS_NUMBER_TO_BIB_ID_MAPPING

    SYS_NUMBER_TO_BIB_ID_MAPPING = sys_number_to_bib_number_mapping

    subscriptions, subscription_histories = fetch_data(credentials)

    subscription_columns = ['biblionumber', 'subscriptionid', 'aqbudgetid', 'librarian', 'startdate', 'aqbooksellerid',
                            'cost', 'weeklength', 'monthlength', 'numberlength', 'periodicity', 'countissuesperunit',
                            'status', 'lastvalue1', 'innerloop1', 'lastvalue2', 'innerloop2', 'lastvalue3',
                            'innerloop3', 'firstacquidate', 'manualhistory', 'irregularity', 'skip_serialseq',
                            'letter', 'numberpattern', 'locale', 'distributedto', 'internalnotes', 'callnumber',
                            'location', 'branchcode', 'lastbranch', 'serialsadditems', 'staffdisplaycount',
                            'opacdisplaycount', 'graceperiod', 'enddate', 'closed', 'reneweddate', 'itemtype',
                            'previousitemtype']
    write_data(subscriptions, 'subscription', subscription_columns)

    history_columns = ['biblionumber', 'subscriptionid', 'histstartdate', 'histenddate', 'missinglist', 'recievedlist',
                       'opacnote', 'librariannote']
    write_data(subscription_histories, 'subscriptionhistory', history_columns)
    logger.info(f'Missing budgets Z16_DOC_NUMBER ' 
                f'{len(missing_budget)} of {len(subscriptions.keys())}, defaulted to fallback budgets:')
    for (z16_doc_number, z68_rec_key) in missing_budget:
        logger.info(f'{z16_doc_number}')


if __name__ == '__main__':

    if len(sys.argv) != 3:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.error('2) Path to mapping Zenon ID -> Koha bibliographic ID.')
        sys.exit()

    with open(sys.argv[2], 'rb') as output_file:
        sys_number_mapping = pickle.load(output_file)

    start(sys.argv[1], sys_number_mapping)
