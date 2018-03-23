import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s-%(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LIBRARY_KEY_MAPPING = {
    'BAYS':  'BASSM',
    'BSA':   'BBSA',
    'LUBL':  'BIAUL',
    'ZADAR': 'BICUAZ',
    'SCHW':  'BLDMV',
    'WINCK': 'BWINCK',
    'ATHEN': 'DAIA',
    'BONN':  'DAIB',
    'DAMAS': 'DAID',
    'EURAS': 'DAIE',
    'RGK':   'DAIF',
    'DAI':   'DAIG',
    'ISTAN': 'DAII',
    'KAIRO': 'DAIK',
    'MADRD': 'DAIM',
    'ORIEN': 'DAIO',
    'PEK':   'DAIP',
    'ROM':   'DAIR',
    'SANAA': 'DAIS',
    'TEHER': 'DAIT',
    'ZENTR': 'DAIZ',
    'DEIA':  'DEIA',
    'DEIJ':  'DEIJ'
}


def map_aleph_key(aleph_key):
    if aleph_key not in LIBRARY_KEY_MAPPING:
        logger.warning('No library key matches: "' + aleph_key + '"')
        return None
    return LIBRARY_KEY_MAPPING[aleph_key]
