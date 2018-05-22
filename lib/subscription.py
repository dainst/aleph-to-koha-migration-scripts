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
                                       '043000_subscription_numberpatterns_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/subscription_numberpatterns_data_import.sql'

FREQUENCY_MAPPING = None
PATTERN_MAPPING = None
SYS_NUMBER_TO_BIB_ID_MAPPING = None
Z00_TO_BIBLIOGRAPHIC_ID_MAPPING = dict()
Z08_DATA = dict()

'''
  `cost` int(11) DEFAULT '0',
  `weeklength` int(11) DEFAULT '0',
  `monthlength` int(11) DEFAULT '0',
  `numberlength` int(11) DEFAULT '0',
  `countissuesperunit` int(11) NOT NULL DEFAULT '1',
  `notes` mediumtext COLLATE utf8_unicode_ci,
  `status` varchar(100) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `lastvalue1` int(11) DEFAULT NULL,
  `innerloop1` int(11) DEFAULT '0',
  `lastvalue2` int(11) DEFAULT NULL,
  `innerloop2` int(11) DEFAULT '0',
  `lastvalue3` int(11) DEFAULT NULL,
  `innerloop3` int(11) DEFAULT '0',
  `manualhistory` tinyint(1) NOT NULL DEFAULT '0',
  `irregularity` text COLLATE utf8_unicode_ci,
  `skip_serialseq` tinyint(1) NOT NULL DEFAULT '0',
  `letter` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `locale` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
  `distributedto` text COLLATE utf8_unicode_ci,
  `callnumber` text COLLATE utf8_unicode_ci,
  `serialsadditems` tinyint(1) NOT NULL DEFAULT '0',
  `graceperiod` int(11) NOT NULL DEFAULT '0',
  `closed` int(1) NOT NULL DEFAULT '0',
  `reneweddate` date DEFAULT NULL,
'''


def parse_z16(parsed_results, data):
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
        koha_bib_id = None

    result['biblionumber'] = koha_bib_id
    result['branchcode'] = library_keys.map_aleph_key(data[2].strip())
    result['startdate'] = date_helper.process_aleph_date(data[3])  # TODO: Check if this is a valid interpretation
    result['firstacquidate'] = date_helper.process_aleph_date(data[3])  # ^---

    result['itemtype'] = 'CR'
    result['internalnotes'] = data[24]

    if data[4] == '20991231':
        end_date = None
    else:
        end_date = date_helper.process_aleph_date(data[4])
    result['enddate'] = end_date

    result['location'] = marc_mapping.map_shelving_location(data[13], koha_bib_id)

    if doc_key in PATTERN_MAPPING:
        result['numberpattern'] = PATTERN_MAPPING[doc_key]
    else:
        logger.warning('No number pattern for Aleph subscription (Z16): %s.' % data[0])

    if doc_key in FREQUENCY_MAPPING:
        result['periodicity'] = FREQUENCY_MAPPING[doc_key]
    else:
        logger.warning('No periodicity information for Aleph subscription (Z16): %s.' % data[0])

    bookseller = mariadb.get_aqbookseller_by_aleph_vendor_key(data[5])
    if bookseller is None:
        logger.warning('No bookseller found for Aleph vendor code "%s". Aleph subscription (Z16): %s.'
                       % (data[5], data[0]))
    else:
        result['aqbooksellerid'] = bookseller[0]

    return parsed_results


def fetch_data(credentials):
    global FREQUENCY_MAPPING
    global PATTERN_MAPPING
    global Z00_TO_BIBLIOGRAPHIC_ID_MAPPING

    with open(script_dir + '/subscription_frequencies_mapping.pickle', 'rb') as mapping_file:
        FREQUENCY_MAPPING = pickle.load(mapping_file)
    with open(script_dir + '/subscription_patterns_mapping.pickle', 'rb') as mapping_file:
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

    return subscriptions


def start(credentials, id_mapping_file):
    global SYS_NUMBER_TO_BIB_ID_MAPPING

    with open(id_mapping_file, 'rb') as id_mapping_file:
        SYS_NUMBER_TO_BIB_ID_MAPPING = pickle.load(id_mapping_file)

    subscriptions = fetch_data(credentials)


if __name__ == '__main__':

    if len(sys.argv) != 3:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.info('2) Pickle with bibliographic id mapping.')
        sys.exit()

    start(sys.argv[1], sys.argv[2])
