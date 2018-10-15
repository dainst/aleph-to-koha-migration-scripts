import lib.mappings.method_of_acquisition as moa
import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

CODES = [
    'Aleph-Geschenk',
    'Alept-Tausch',
    'Aleph-Ansicht',
    'Aleph-Kauffrei',
    'Aleph-Andere',
    'Aleph-Kauf',
    'Aleph-Pflicht'
]

ACQUISITION_METHOD_MAPPING = {
    'A': 'Aleph-Ansicht',
    'P': 'Aleph-Kauf',
    'PF': 'Aleph-Kauffrei',
    'G': 'Aleph-Geschenk',
    'E': 'Alept-Tausch',
    'D': 'Aleph-Pflicht',
    'O': 'Aleph-Andere'
}


def get_budget_for_method_of_acquisition(method_of_acquisition):
    if set(ACQUISITION_METHOD_MAPPING.keys()) != set(moa.METHODS.keys()):
        logger.warning(f'Differing number of acquisition method keys between {__name__} and {moa.__name__}!')
        logger.warning(f'{ACQUISITION_METHOD_MAPPING.keys()} vs. {moa.METHODS.keys()}.')

    return ACQUISITION_METHOD_MAPPING[method_of_acquisition]
