import logging
import sys
import pickle

from lib import aqbooksellers, aqcontacts, aqbudgets_and_aqbudgetperiods, aqbasketgroups, aqbasket, aqinvoices, \
    subscription_frequencies, subscription_numberpatterns, subscription, aqorders

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':

    if len(sys.argv) != 2:
        logger.error('Please provide as argument:')
        logger.error('1) Connection info and credentials, pattern: "%USER%/%PASSWORD%@%IP%/%SID%".')
        logger.error('2) Estimated system number to Koha bibliography number mapping.')
        sys.exit()

    with open('./pickles/estimated_sys_number_to_bibliographic_number_mapping.pickle', 'rb') as id_mapping_file:
        estimated_sys_number_to_bibliographic_number_mapping = pickle.load(id_mapping_file)

    aqbudgets_and_aqbudgetperiods.start(sys.argv[1])
    aqbooksellers.start(sys.argv[1])
    aqcontacts.start(sys.argv[1])
    aqbasketgroups.start(sys.argv[1])
    aqbasket.start(sys.argv[1])
    aqinvoices.start(sys.argv[1])
    subscription_frequencies.start(sys.argv[1])
    subscription_numberpatterns.start(sys.argv[1])
    subscription.start(sys.argv[1], estimated_sys_number_to_bibliographic_number_mapping)
    aqorders.start(sys.argv[1])
