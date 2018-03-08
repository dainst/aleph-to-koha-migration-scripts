import logging
import sys
import os

import lib.database_connections.oracle as oracle
import lib.database_connections.mariadb as mariadb
import lib.oracle_helper.dates as dates_helper
import lib.mappings.currency as currency
import lib.mappings.order_status as order_status_helper

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MISSING_ITEM_DATA = []
MISSING_BASKET = []


def get_biblionumber(key, z30_data):
    if key in z30_data:
        return z30_data[key][0][0:9]


def process_open_order(data):
    result = dict()

    result['currency'] = currency.map_from_currency(data[33], True)
    result['unitprice'] = data[31]
    result['unitprice_tax_included'] = data[31]
    result['listprice'] = data[34]
    result['ecost'] = data[37]
    result['ecost_tax_included'] = data[37]
    result['uncertainprice'] = 1
    # result['discount'] =
    return result


def process_z68_data(previous_results, z30_data, basket_data, data):

    aleph_rec_key = data[0]

    basket_no = None
    if aleph_rec_key in basket_data:
        basket_no = basket_data[aleph_rec_key][0]

    if basket_no is None:
        MISSING_BASKET.append(data)

    order_status = order_status_helper.map_aleph_key(data[7])
    datereceived = None
    if order_status == 'complete':
        datereceived = dates_helper.process_aleph_date(data[8])

    result = {
        'order_status': order_status,
        'datereceived': datereceived,
        'order_internalnote': data[24],
        'suppliers_reference_number': data[26],
        'order_vendornote': data[27],
        'basketno': basket_no,
        'budget_id': 1,
        'biblionumber': get_biblionumber(data[2].strip(), z30_data),
        'quantity': data[30]
    }

    if result['biblionumber'] is None:
        MISSING_ITEM_DATA.append(data)
        return previous_results

    if order_status_helper.is_open(data[7]):
        result = {**result, **process_open_order(data)}

    previous_results[aleph_rec_key] = result

    return previous_results

    # `entrydate` date DEFAULT NULL,
    # `quantity` smallint(6) DEFAULT NULL,
    # `listprice` decimal(28,6) DEFAULT NULL,
    # `invoiceid` int(11) DEFAULT NULL, # TODO
    # `freight` decimal(28,6) DEFAULT NULL,
    # `quantityreceived` smallint(6) NOT NULL DEFAULT 0,
    # `datecancellationprinted` date DEFAULT NULL,
    # `cancellationreason` text COLLATE utf8_unicode_ci DEFAULT NULL,
    # `purchaseordernumber` mediumtext COLLATE utf8_unicode_ci DEFAULT NULL,
    # `rrp` decimal(13,2) DEFAULT NULL,
    # `rrp_tax_excluded` decimal(28,6) DEFAULT NULL,
    # `rrp_tax_included` decimal(28,6) DEFAULT NULL,
    # `tax_rate_bak` decimal(6,4) DEFAULT NULL,
    # `tax_rate_on_ordering` decimal(6,4) DEFAULT NULL,
    # `tax_rate_on_receiving` decimal(6,4) DEFAULT NULL,
    # `tax_value_bak` decimal(28,6) DEFAULT NULL,
    # `tax_value_on_ordering` decimal(28,6) DEFAULT NULL,
    # `tax_value_on_receiving` decimal(28,6) DEFAULT NULL,
    # `discount` float(6,4) DEFAULT NULL,
    # `sort1` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `sort2` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `sort1_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `sort2_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `uncertainprice` tinyint(1) DEFAULT NULL,
    # `claims_count` int(11) DEFAULT 0,
    # `claimed_date` date DEFAULT NULL,
    # `subscriptionid` int(11) DEFAULT NULL, # TODO
    # `parent_ordernumber` int(11) DEFAULT NULL,
    # `line_item_id` varchar(35) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `suppliers_reference_number` varchar(35) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `suppliers_reference_qualifier` varchar(3) COLLATE utf8_unicode_ci DEFAULT NULL,
    # `suppliers_report` text COLLATE utf8_unicode_ci DEFAULT NULL,
    # `ALEPH_Z68_DOC_NUMBER` varchar(25) NOT NULL,


def fetch_data(credentials):
    logger.info('Connecting...')
    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    logger.info('Connected.')

    logger.info('Fetching z30 data (items)...')
    z30_data = dict()
    z30_data_cursor = oracle.get_z30_with_order_number()
    for query_result in z30_data_cursor:
        z30_data[query_result[24].strip()] = query_result
    z30_data_cursor.close()
    logger.info('Done.')

    logger.info('Fetching basket data...')
    basket_data = dict()
    basket_data_cursor = mariadb.get_aqbaskets()
    for query_result in basket_data_cursor:
        basket_data[query_result[-1]] = query_result
    logger.info('Done.')

    results = dict()
    data_cursor = oracle.get_not_cancelled_z68()

    for query_result in data_cursor:
        results = process_z68_data(results, z30_data, basket_data, query_result)
    data_cursor.close()

    oracle.close_connection()

    return results


def start(oracle_credentials):
    results = fetch_data(oracle_credentials)
    # filtered_results = conflate_duplicates(results)
    # write_data(filtered_results)
    logger.warning('%s Z68-orders have no matching Z30-items:', len(MISSING_ITEM_DATA))
    for missing in MISSING_ITEM_DATA:
        logger.warning(missing)

    logger.warning('%s Z68-orders have no matching basket:', len(MISSING_BASKET))
    for missing in MISSING_BASKET:
        logger.warning(missing)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
