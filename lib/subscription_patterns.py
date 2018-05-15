import logging
import sys
import os
import re

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.mappings.library_keys as library_keys
import lib.oracle_helper.dates as dates_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

'''
SUBSCRIPTION
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
  `branchcode` varchar(10) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
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

'''
NUMBERPATTERNS
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `label` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `displayorder` int(11) DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci NOT NULL,
  `numberingmethod` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `label1` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `add1` int(11) DEFAULT NULL,
  `every1` int(11) DEFAULT NULL,
  `whenmorethan1` int(11) DEFAULT NULL,
  `setto1` int(11) DEFAULT NULL,
  `numbering1` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `label2` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `add2` int(11) DEFAULT NULL,
  `every2` int(11) DEFAULT NULL,
  `whenmorethan2` int(11) DEFAULT NULL,
  `setto2` int(11) DEFAULT NULL,
  `numbering2` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `label3` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `add3` int(11) DEFAULT NULL,
  `every3` int(11) DEFAULT NULL,
  `whenmorethan3` int(11) DEFAULT NULL,
  `setto3` int(11) DEFAULT NULL,
  `numbering3` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
'''

MAX_NUMBER_PATTERN_VALUE = 99999
UNHANDLED_PATTERNS = []

SINGLE_VARIABLE_PATTERN = re.compile('^(.*)\$(.)(.*)$')
TWO_VARIABLES_PATTERN = re.compile('^(.*)\$(.)(.*)\$(.)(.*)$')


def handle_two_variable_pattern(previous_results, data):
    global UNHANDLED_PATTERNS

    result = dict()

    aleph_pattern = data[2].upper()
    koha_pattern = None
    match = TWO_VARIABLES_PATTERN.match(aleph_pattern)
    first_variable_type = None
    second_variable_type = None

    # In Koha, the variables in the pattern are {X}, {Y}, {Z}
    # while in Aleph $Y denotes a year, $V a volume etc. So Koha is more generic. Also, if $Y is the "highest order"
    # variable, it has to be represented as {X}
    if match is not None:
        (first_variable_type, second_variable_type) = (match.group(2), match.group(4))
        if first_variable_type == 'Y':
            if second_variable_type == 'V':
                result['label'] = '%sJahr%sBand%s' % (match.group(1), match.group(3), match.group(5))
                result['label2'] = 'Band'
                # result['add2'] =
            result['label1'] = 'Band'
            result['add1'] = 1
            result['every1'] = data[9]
            result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE
            result['numberingmethod'] = koha_pattern

            koha_pattern = '%s{X}%s{Y}%s' % (match.group(1), match.group(3), match.group(5))
        elif second_variable_type == 'Y':
            koha_pattern = '%s{Y}%s{X}%s' % (match.group(1), match.group(3), match.group(5))
    else:
        UNHANDLED_PATTERNS.append(aleph_pattern)
        return previous_results

    result['numberingmethod'] = koha_pattern

    return previous_results


def handle_single_variable_pattern(previous_results, data):
    global MAX_NUMBER_PATTERN_VALUE
    global UNHANDLED_PATTERNS
    global SINGLE_VARIABLE_PATTERN

    aleph_pattern = data[2].upper()
    koha_pattern = None
    match = SINGLE_VARIABLE_PATTERN.match(aleph_pattern)

    result = dict()

    if match is not None:
        koha_pattern = '%s{X}%s' % (match.group(1), match.group(3))
        variable_type = match.group(2)
        if variable_type == 'Y':
            result['label'] = '%sJahr%s' % (match.group(1), match.group(3))
            result['label1'] = 'Jahr'
        elif variable_type == 'V':
            result['label'] = '%sBand%s' % (match.group(1), match.group(3))
            result['label1'] = 'Band'
        else:
            UNHANDLED_PATTERNS.append(data[2])
            return previous_results

    result['add1'] = 1
    result['every1'] = 1
    result['whenmorethan1'] = MAX_NUMBER_PATTERN_VALUE
    result['numberingmethod'] = koha_pattern

    index_set = tuple(result.values())

    result['Z08_REC_KEY'] = data[0]
    if index_set in previous_results:
        previous_results[index_set].append(result)
    else:
        previous_results[index_set] = [result]

    return previous_results


def parse_numbering_pattern(previous_results, data):
    global UNHANDLED_PATTERNS

    aleph_pattern = data[2].upper()

    variable_count = sum(c == '$' for c in aleph_pattern)
    if variable_count > 2:
        if data[2] not in UNHANDLED_PATTERNS:
            UNHANDLED_PATTERNS.append(aleph_pattern)
        return previous_results
    elif variable_count == 2:
        return handle_two_variable_pattern(previous_results, data)
    else:
        return handle_single_variable_pattern(previous_results, data)


def fetch_data(credentials):

    oracle.establish_connection(credentials)

    cursor = oracle.get_z08_data()
    numbering_patterns_data = dict()

    for row in cursor:
        numbering_patterns_data = parse_numbering_pattern(numbering_patterns_data, row)

    cursor.close()

    print(numbering_patterns_data)

    print('Unhandled patterns: ')
    for pattern in UNHANDLED_PATTERNS:
        print(pattern)

    logger.debug('Todo')


def start(credentials):
    fetch_data(credentials)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
