import logging
import sys

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def construct_name(query_result):
    return "[ALEPH-order]" + query_result[0]


def process_68_data(query_result):

    result = dict()

    vendor_key = query_result[25]

    if vendor_key is None:
        logger.warning('Vendor key in Z68 is None, Z68_REC_KEY:')
        logger.warning(' ' + query_result[0])
        logger.warning(' Skipping order.')
        return None

    result['ALEPH_REC_KEY'] = query_result[0]
    result['name'] = construct_name(query_result)
    result['closed'] = False
    result['booksellerid'] = mariadb.get_aqbookseller_by_aleph_key(vendor_key)[0]
    result['deliveryplace'] = library_keys.map_aleph_key(query_result[12].strip())
    result['billingplace'] = library_keys.map_aleph_key(query_result[12].strip())

    return result


def fetch_data(credentials):
    logger.info('Connecting...')
    oracle.establish_connection(credentials)
    mariadb.establish_connection()
    logger.info('Connected...')

    z68_result = []
    z68_data_cursor = oracle.get_open_z68_monograph()
    logger.info('Processing data from z70 table...')
    for query_result in z68_data_cursor:
        z68_result.append(process_68_data(query_result))

    z68_data_cursor.close()

    oracle.close_connection()

    return [result for result in z68_result if result is not None]  # filter None values, caused by missing vendor info

    # Still unhandled fields for aqbookseller:
    # freedeliveryplace 	text 	65535 	 √  		null
    # deliverycomment 	varchar 	255 	 √  		null


def start(credentials):
    results = fetch_data(credentials)

    # TODO: Write data


if __name__ == '__main__':

    import mappings.library_keys as library_keys
    import database_connections.mariadb as mariadb
    import database_connections.oracle as oracle

    if len(sys.argv) != 2:
        logger.info('Please provide as argument:')
        logger.info('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    start(sys.argv[1])
else:
    import aleph_oracle_exports.mappings.library_keys as library_keys
    import aleph_oracle_exports.database_connections.mariadb as mariadb
    import aleph_oracle_exports.database_connections.oracle as oracle
