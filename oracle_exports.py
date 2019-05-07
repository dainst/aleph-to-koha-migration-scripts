import logging
import sys
import pickle

from lib import aqbooksellers, aqcontacts, aqbudgets_and_aqbudgetperiods, aqbasketgroups, aqbasket, \
    subscription_frequencies, subscription_numberpatterns, aqorders, subscription, aqorders_items, serial, aqinvoices

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':

    if len(sys.argv) != 4:
        logger.error('Please provide as argument:')
        logger.error('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.error('2) Mapping Zenon ID -> Koha bibliographic ID.')
        logger.error('3) SQL File containing `items`-table  data exported from Koha.')
        sys.exit()

    aqbudgets_and_aqbudgetperiods.start(sys.argv[1])
    aqbooksellers.start(sys.argv[1])
    aqcontacts.start(sys.argv[1])
    aqbasketgroups.start(sys.argv[1])
    aqbasket.start(sys.argv[1])
    subscription_frequencies.start(sys.argv[1])
    subscription_numberpatterns.start(sys.argv[1])

    with open(sys.argv[2], 'rb') as file1:
        sys_number_mapping = pickle.load(file1)

        aqinvoices.start(sys.argv[1])
        subscription.start(sys.argv[1], sys_number_mapping)
        aqorders.start(sys.argv[1], sys_number_mapping)
        aqorders_items.start(sys.argv[1], sys.argv[3])  # will copy the given SQL file into intermediate value directory

    with open('pickles/order_to_subscription_mapping.pickle', 'rb') as file2:
        order_to_subscription_mapping = pickle.load(file2)
        serial.start(sys.argv[1], order_to_subscription_mapping)
