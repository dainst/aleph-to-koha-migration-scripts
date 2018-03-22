# AUTHORITY_CONTROL_FIELDS_MAPPING, read as:
#   ('marc  authority field number', 'marc bibliographic field number')
#   see also:
#   https://www.loc.gov/marc/authority/
#   https://www.loc.gov/marc/bibliographic/

AUTHORITY_FIELDS_TO_BIBLIOGRAPHIC_FIELDS_MAPPING = [
    ('100', '100'), ('100', '600'), ('100', '700'),  # Personal Name
    ('110', '110'), ('110', '610'), ('110', '710'),  # Corporate Name
    ('111', '111'), ('111', '611'), ('111', '711'),  # Meeting Name
    ('130', '130'), ('130', '630'), ('130', '730'),  # Uniform Title
    ('150', '650'),                                  # Topical Term
    ('151', '651')                                   # Geographic Name
]


Z30_MATERIAL_MAPPING = {
    'ARTIK': 'AN',
    'BUCH': 'BK',
    'CDROM': 'DAV',
    'EBOOK': 'EB',
    'EJOUR': 'EJ',
    'ISSBD': 'CR',
    'ISSUE': 'CR',
    'KART': 'MP',
    'MANUS': 'MA',
    'MBWK': 'MBW',
    'MEDK': 'MX',
    'NBM': 'VM',
    'SDD': 'SD',
    'SERBD': 'BK',
    'SEREB': 'BK',
    'SERIE': 'SE',
    'VIDEO': 'VI',
    'ZSN': 'CR',
    'ZTG': 'CR'
}


def map_material(aleph_material):
    if aleph_material not in Z30_MATERIAL_MAPPING:
        return ''
    else:
        return Z30_MATERIAL_MAPPING[aleph_material]


SHELVING_LOCATION_MAPPING = {
    'AKURG': 'AKURG',
    'ARCHV': 'ARCHV',
    'AS I': 'AS I',
    'AS II': 'AS II',
    'AUSS': 'AUSS',
    'BAGD': 'BAGD',
    'BIB1': 'BIB1',
    'BIB2': 'BIB2',
    'BIBL': 'BIBL',
    'BIBLB': 'BIBL',
    'BIBZ': 'BIBZ',
    'BPEK': 'BIBL',
    'DAMA': 'DAMA',
    'DAM': 'BIBL',
    'DEND': 'DEND',
    'DEP': 'DEP1',
    'DEP2': 'DEP2',
    'DEP3': 'DEP3',
    'DISS': 'DISS',
    'EG': 'EG',
    'FOLIA': 'FOLIA',
    'FOLIO': 'FOLIO',
    'GH': 'GH',
    'GROSS': 'GROSS',
    'HINKL': 'HINKL',
    'KART': 'KART',
    'KARTS': 'KARTS',
    'KOMPA': 'KOMPA',
    'KS I': 'KS I',
    'LESE': 'LESE',
    'MAG': 'MAG',
    'MAGB': 'MAGB',
    'MEDS': 'MEDS',
    'MIKRO': 'MIKRO',
    'MS I': 'MS I',
    'MS II': 'MS II',
    'NATUR': 'NATUR',
    'OG': 'OG',
    'ONL': 'ONL',
    'PERGA': 'GH',

    'RARA': 'RARA',
    'RARA': 'RARAB',

    'RARAH': 'RARAH',
    'SA': 'SA',
    'SANA': 'SANA',
    'SANAA': 'BIBL',
    'SC': 'SC',
    'SEP': 'SEP',
    'SI1': 'SI1',
    'SIII2': 'SIII2',
    'SK': 'KART',

    'SOND': 'SEP',
    'SOND': 'SOND',

    'SONDS': 'SEP',
    'SR01': 'SR01',
    'SR10': 'SR10',
    'SR11': 'SR11',
    'SR13': 'SR13',
    'SR14': 'SR14',
    'SR21': 'SR21',
    'SR23': 'SR23',
    'SR31': 'SR31',
    'STEA': 'EURAS',
    'SVER': 'SVER',
    'SVI': 'SVI',
    'SVII': 'SVII',
    'UG': 'UG',
    'URUK': 'URUK',
    'ZADAR': 'ZADAR',
    'ZBIB': 'BIBZ'
}

def map_shelving_location(aleph_z30_collection):
    if aleph_z30_collection not in SHELVING_LOCATION_MAPPING:
        return ''
    else:
        return SHELVING_LOCATION_MAPPING[aleph_z30_collection]
