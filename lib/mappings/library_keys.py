LIBRARY_KEY_MAPPING = {
    'BAYS':  'BASSM',
    'BSA':   'BBSA',
    'WINCK': 'BWINCK',
    'ZADAR': 'BICUAZ',
    'ATHEN': 'DAIA',
    'EURAS': 'DAIE',
    'DAI':   'DAIG',
    'ISTAN': 'DAII',
    'BONN':  'DAIB',
    'KAIRO': 'DAIK',
    'MADRD': 'DAIM',
    'ORIEN': 'DAIO',
    'RGK':   'DAIF',
    'ROM':   'DAIR',
    'ZENTR': 'DAIZ',
    'DAMAS': 'DAID',
    'PEK':   'DAIP',
    'SANAA': 'DAIS',
    'TEHER': 'DAIT',
    'DEIA':  'DEIA',
    'DEIJ':  'DEIJ',
    'LUBL':  'BIAUL',
    'SCHW':  'BLDMV'
}


def map_aleph_key(aleph_key):
    return LIBRARY_KEY_MAPPING[aleph_key]
