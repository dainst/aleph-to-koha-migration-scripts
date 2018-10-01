import logging
import sys

from lib import aqbooksellers, aqcontacts, aqbudgets_and_aqbudgetperiods, aqbasketgroups, aqbasket, \
    subscription_frequencies, subscription_numberpatterns

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.error('Please provide as argument:')
        logger.error('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    aqbudgets_and_aqbudgetperiods.start(sys.argv[1])
    aqbooksellers.start(sys.argv[1])
    aqcontacts.start(sys.argv[1])
    aqbasketgroups.start(sys.argv[1])
    aqbasket.start(sys.argv[1])
    subscription_frequencies.start(sys.argv[1])
    subscription_numberpatterns.start(sys.argv[1])
