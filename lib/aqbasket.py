import sys
import logging

import lib.database_connections.mariadb as mariadb
import lib.database_connections.oracle as oracle

import lib.mappings.library_keys as library_keys
import lib.mappings.method_of_acquisition as method_of_acquisition

import lib.oracle_helper.dates as dates_helper
import lib.oracle_helper.z68 as z68

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def evaluate_is_standing(aleph_order_type):
    aleph_order_type = aleph_order_type.strip()

    if aleph_order_type == 'O':
        return 1

    return 0


''' Still unset in Koha:
contractnumber 	int 	10 	 √  		null 		
aqcontract 	links this basket to the aqcontract table (aqcontract.contractnumber)
authorisedby 	varchar 	10 	 √  		null 			the borrowernumber of the person who created the basket
booksellerinvoicenumber 	mediumtext 	16777215 	 √  		null 			appears to always be NULL
create_items 	enum 	11 	 √  		null 			when items should be created for orders in this basket
'''


def process_z68_data(previous_results, query_result):
    result = dict()
    # aleph: integer YYYYMMDD
    # koha: date YYYY-MM-DD

    parsed_open_date = dates_helper.process_aleph_date(query_result[6])
    if parsed_open_date is not None:
        result['creationdate'] = parsed_open_date

    if query_result[12] is None or library_keys.map_aleph_key(query_result[12].strip()) is None:
        logger.warning('No branch information for order ' + query_result[0] + '. Skipping...')
        return previous_results

    result['deliveryplace'] = library_keys.map_aleph_key(query_result[12].strip())
    result['billingplace'] = library_keys.map_aleph_key(query_result[12].strip())
    result['branch'] = library_keys.map_aleph_key(query_result[12].strip())

    if query_result[14] is not None:
        result['note'] = 'Erwerbungsart: ' + method_of_acquisition.map_aleph_key(query_result[14].strip())

    parsed_order_date = dates_helper.process_aleph_date(query_result[15])
    if parsed_order_date is not None:
        result['closedate'] = parsed_order_date
    else:
        result['closedate'] = None

    result['booksellernote'] = query_result[51]
    result['is_standing'] = z68.evaluate_is_standing(query_result[1])

    basketgroup = mariadb.get_aqbasketgroup_by_aleph_doc_number(query_result[0][0:9])

    result['basketgroupid'] = basketgroup[0]
    result['booksellerid'] = basketgroup[3]
    result['basketname'] = 'order-sequence:' + query_result[0][9:]

    previous_results[query_result[0]] = result


    logger.debug(result)


    return previous_results


def fetch_data(credentials):
    logger.info('Connecting...')
    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    logger.info('Connected...')

    z68_result = dict()
    z68_data_cursor = oracle.get_open_z68_monograph()
    logger.info('Processing data from z68 table...')
    for query_result in z68_data_cursor:
        z68_result = process_z68_data(z68_result, query_result)

    z68_data_cursor.close()

    oracle.close_connection()


def start(credentials):
    results = fetch_data(credentials)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
