import logging
import sys
import os
import re
import pickle

import lib.database_connections.oracle as oracle
import lib.mappings.library_keys as library_keys
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.z08 as z08_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_dir = os.path.dirname(__file__)

MAPPING_SQL_OUTPUT_PATH = script_dir + '/mariadb_intermediate_values/' \
                                       '043000_subscription_numberpatterns_data_mapping.sql'
IMPORT_SQL_OUTPUT_PATH = script_dir + '/ready_for_import/subscription_numberpatterns_data_import.sql'

FREQUENCY_MAPPING = None
PATTERN_MAPPING = None

'''
  `biblionumber` int(11) NOT NULL DEFAULT '0',
  `subscriptionid` int(11) NOT NULL AUTO_INCREMENT,
  `librarian` varchar(100) COLLATE utf8_unicode_ci DEFAULT '',
  `startdate` date DEFAULT NULL,
  `aqbooksellerid` int(11) DEFAULT '0',
  `cost` int(11) DEFAULT '0',
  `aqbudgetid` int(11) DEFAULT '0',
  `weeklength` int(11) DEFAULT '0',
  `monthlength` int(11) DEFAULT '0',
  `numberlength` int(11) DEFAULT '0',
  `periodicity` int(11) DEFAULT NULL,
  `countissuesperunit` int(11) NOT NULL DEFAULT '1',
  `notes` mediumtext COLLATE utf8_unicode_ci,
  `status` varchar(100) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `lastvalue1` int(11) DEFAULT NULL,
  `innerloop1` int(11) DEFAULT '0',
  `lastvalue2` int(11) DEFAULT NULL,
  `innerloop2` int(11) DEFAULT '0',
  `lastvalue3` int(11) DEFAULT NULL,
  `innerloop3` int(11) DEFAULT '0',
  `firstacquidate` date DEFAULT NULL,
  `manualhistory` tinyint(1) NOT NULL DEFAULT '0',
  `irregularity` text COLLATE utf8_unicode_ci,
  `skip_serialseq` tinyint(1) NOT NULL DEFAULT '0',
  `letter` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `numberpattern` int(11) DEFAULT NULL,
  `locale` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
  `distributedto` text COLLATE utf8_unicode_ci,
  `internalnotes` longtext COLLATE utf8_unicode_ci,
  `callnumber` text COLLATE utf8_unicode_ci,
  `location` varchar(80) COLLATE utf8_unicode_ci DEFAULT '',
  `lastbranch` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `serialsadditems` tinyint(1) NOT NULL DEFAULT '0',
  `staffdisplaycount` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `opacdisplaycount` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `graceperiod` int(11) NOT NULL DEFAULT '0',
  `enddate` date DEFAULT NULL,
  `closed` int(1) NOT NULL DEFAULT '0',
  `reneweddate` date DEFAULT NULL,
  `itemtype` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `previousitemtype` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
'''


def parse_z16(parsed_results, data):
    global FREQUENCY_MAPPING
    global PATTERN_MAPPING

    result = dict()

    result['branchcode'] = library_keys.map_aleph_key(data[2].strip())

    doc_key = data[0][0:9]

    if doc_key in PATTERN_MAPPING:
        result['numberpattern'] = PATTERN_MAPPING[data[0][0:9]]

    if doc_key in FREQUENCY_MAPPING:
        result['periodicity'] = FREQUENCY_MAPPING[data[0][0:9]]

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

    with open(script_dir + '/subscription_frequencies_mapping.pickle', 'rb') as mapping_file:
        FREQUENCY_MAPPING = pickle.load(mapping_file)
    with open(script_dir + '/subscription_patterns_mapping.pickle', 'rb') as mapping_file:
        PATTERN_MAPPING = pickle.load(mapping_file)

    oracle.establish_connection(credentials)
    mariadb.establish_connection()

    cursor = oracle.get_subscription_data()
    subscriptions = dict()
    for row in cursor:
        subscriptions = parse_z16(subscriptions, row)
    cursor.close()

    return subscriptions


def start(credentials):
    subscriptions = fetch_data(credentials)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
