import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

METHODS = {
    'A': 'zur Ansicht',
    'P': 'Kauf',
    'PF': 'Kauf (frei)',
    'G': 'Geschenk',
    'E': 'Tausch',
    'D': 'Pflicht',
    'O': 'Andere'
}


def map_aleph_key(aleph_key):
    if aleph_key not in METHODS:
        logger.warning("Unknown method of acquisition key: " + aleph_key + ", defaulting to " + METHODS['O'])
        return METHODS['O']
    return METHODS[aleph_key]
