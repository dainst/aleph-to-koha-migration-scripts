import logging
import sys
import pickle

from lib import aqorders, subscription, aqorders_items, serial, aqinvoices

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':

    if len(sys.argv) != 4:
        logger.error('Please provide as argument:')
        logger.error('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.error('2) Mapping Zenon ID -> Koha bibliographic ID.')
        logger.error('3) File containing item SQL data exported from Koha.')
        sys.exit()

    with open(sys.argv[2], 'rb') as output_file:
        sys_number_mapping = pickle.load(output_file)

    aqinvoices.start(sys.argv[1])
    subscription.start(sys.argv[1], sys_number_mapping)
    # aqorders.start(sys.argv[1], sys_number_mapping)
    # aqorders_items.start(sys.argv[1], sys.argv[3])  # will copy the given SQL file into intermediate value directory
    # serial.start(sys.argv[1])

