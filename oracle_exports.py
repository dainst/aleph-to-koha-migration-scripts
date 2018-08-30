import logging
import sys
from lib import aqbooksellers, aqcontacts, aqbasketgroups, aqbasket, aqbudgets_and_aqbudgetperiods, aqinvoices
from lib import subscription_frequencies, subscription_numberpatterns, subscription, aqorders, aqorders_items
from lib import serial

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':

    if len(sys.argv) != 3:
        logger.error('Please provide as argument:')
        logger.error('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.error('2) File containing item SQL data exported from Koha.')
        sys.exit()

    aqbudgets_and_aqbudgetperiods.start(sys.argv[1])
    aqbooksellers.start(sys.argv[1])
    aqcontacts.start(sys.argv[1])
    aqbasketgroups.start(sys.argv[1])
    aqbasket.start(sys.argv[1])
    aqinvoices.start(sys.argv[1])
    subscription_frequencies.start(sys.argv[1])
    subscription_numberpatterns.start(sys.argv[1])
    subscription.start(sys.argv[1])
    aqorders.start(sys.argv[1])
    aqorders_items.start(sys.argv[1], sys.argv[2])  # will copy the given SQL file into intermediate value directory
    serial.start(sys.argv[1])

