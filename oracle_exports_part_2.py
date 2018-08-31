import logging
import sys

from lib import aqorders_items, serial
import bibliography_id_mapping

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':

    if len(sys.argv) != 4:
        logger.error('Please provide as argument:')
        logger.error('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.error('2) File containing item SQL data exported from Koha.')
        sys.exit()

    aqorders_items.start(sys.argv[1], sys.argv[3])  # will copy the given SQL file into intermediate value directory
    serial.start(sys.argv[1])

