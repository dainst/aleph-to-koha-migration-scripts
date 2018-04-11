import logging
import sys
from lib import aqbooksellers, aqcontacts, aqbasketgroups, aqbasket, aqbudgetperiods, aqbudgets

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.error('Please provide as argument:')
        logger.error('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        sys.exit()

    aqbudgetperiods.start(sys.argv[1])
    aqbooksellers.start(sys.argv[1])
    aqbudgets.start(sys.argv[1])
    aqcontacts.start(sys.argv[1])
    aqbasketgroups.start(sys.argv[1])
    aqbasket.start(sys.argv[1])
