import logging
import sys
import pickle

from lib import aqorders, subscription, aqorders_items, serial, aqinvoices

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



'''
1) Export items.sql after having imported bibliographic data into Koha using:
mysqldump --user=<user> --host=localhost --password=<pw> --port=37835 --default-character-set=utf8 --single-transaction=TRUE --no-create-info=TRUE --skip-triggers "<database>" items > items.sql
2) Run bibliography_id_mapping.py beforehand, in order to create the Zenon ID -> Koha bibliographic ID mapping."
'''

if __name__ == '__main__':

    if len(sys.argv) != 4:
        logger.error('Please provide as argument:')
        logger.error('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.error('2) Mapping Zenon ID -> Koha bibliographic ID.')
        logger.error('3) SQL File containing `items`-table  data exported from Koha.')
        sys.exit()

    with open(sys.argv[2], 'rb') as file1:
        sys_number_mapping = pickle.load(file1)

        aqinvoices.start(sys.argv[1])
        subscription.start(sys.argv[1], sys_number_mapping)
        aqorders.start(sys.argv[1], sys_number_mapping)
        aqorders_items.start(sys.argv[1], sys.argv[3])  # will copy the given SQL file into intermediate value directory

    with open('pickles/order_to_subscription_mapping.pickle', 'rb') as file2:
        order_to_subscription_mapping = pickle.load(file2)
        serial.start(sys.argv[1], order_to_subscription_mapping)
