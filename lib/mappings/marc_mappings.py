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
        return None
    else:
        return Z30_MATERIAL_MAPPING[aleph_material]


SHELVING_LOCATION_MAPPING = {
    ('AKURG', 'DAII'): 'AKURG',
    ('ARCHV', 'DAIB'): 'ARCHV',
    ('ARCHV', 'DAIM'): 'ARCHV',
    ('ARCHV', 'DAIZ'): 'ARCHV',
    ('AS I', 'DAIB'): 'AS I',
    ('AS II', 'DAIB'): 'AS II',
    ('AUSS', 'BWINCK'): 'AUSS',
    ('BAGD', 'DAIO'): 'BAGD',
    ('BIB1', 'DAIE'): 'BIB1',
    ('BIB2', 'DAIE'): 'BIB2',
    ('BIBL', 'BASSM'): 'BIBL',
    ('BIBL', 'BIAUL'): 'BIBL',
    ('BIBL', 'BICUAZ'): 'BIBL',
    ('BIBL', 'BLDMV'): 'BIBL',
    ('BIBL', 'BWINCK'): 'BIBL',
    ('BIBL', 'DAIF'): 'BIBL',
    ('BIBL', 'DAIK'): 'BIBL',
    ('BIBL', 'DAIO'): 'BIBL',
    ('BIBLB', 'DAII'): 'BIBL',
    ('BIBZ', 'DAIE'): 'BIBZ',
    ('BPEK', 'DAIP'): 'BIBL',
    ('DAMA', 'DAIO'): 'DAMA',
    ('DAM', 'DAID'): 'BIBL',
    ('DEND', 'DAIE'): 'DEND',
    ('DEP', 'DAIA'): 'DEP1',
    ('DEP2', 'DAIA'): 'DEP2',
    ('DEP3', 'DAIA'): 'DEP3',
    ('DISS', 'DAIF'): 'DISS',
    ('EG', 'DAIF'): 'EG',
    ('FOLIA', 'DAIB'): 'FOLIA',
    ('FOLIO', 'DAIZ'): 'FOLIO',
    ('GH', 'DAII'): 'GH',
    ('GH', 'DAIK'): 'GH',
    ('GROSS', 'DAIF'): 'GROSS',
    ('GROSS', 'DAII'): 'GROSS',
    ('GROSS', 'DAIK'): 'GROSS',
    ('GROSS', 'DAIO'): 'GROSS',
    ('GROSS', 'DAIZ'): 'GROSS',
    ('HINKL', 'DAIZ'): 'HINKL',
    ('KART', 'DAII'): 'KART',
    ('KART', 'DAIK'): 'KART',
    ('KART', 'DAIO'): 'KART',
    ('KARTS', 'DAIF'): 'KARTS',
    ('KARTS', 'DAIZ'): 'KARTS',
    ('KOMPA', 'DAIE'): 'KOMPA',
    ('KS I', 'DAIB'): 'KS I',
    ('LESE', 'BBSA'): 'LESE',
    ('LESE', 'DAII'): 'LESE',
    ('LESE', 'DEIA'): 'LESE',
    ('LESE', 'DEIJ'): 'LESE',
    ('MAG', 'DAIB'): 'MAG',
    ('MAG', 'DAIF'): 'MAG',
    ('MAG', 'DAII'): 'MAG',
    ('MAGB', 'DAID'): 'MAGB',
    ('MAGB', 'DAIS'): 'MAGB',
    ('MEDS', 'DAIE'): 'MEDS',
    ('MEDS', 'DAIF'): 'MEDS',
    ('MEDS', 'DAIZ'): 'MEDS',
    ('MIKRO', 'DAII'): 'MIKRO',
    ('MS I', 'DAIB'): 'MS I',
    ('MS II', 'DAIB'): 'MS II',
    ('NATUR', 'DAIE'): 'NATUR',
    ('OG', 'DAIF'): 'OG',
    ('ONL', 'DAIF'): 'ONL',
    ('PERGA', 'DAII'): 'GH',
    ('RARA', 'BWINCK'): 'RARA',
    ('RARA', 'DAIE'): 'RARA',
    ('RARA', 'DAIF'): 'RARA',
    ('RARA', 'DAII'): 'RARA',
    ('RARA', 'DAIM'): 'RARA',
    ('RARA', 'DAIO'): 'RARA',
    ('RARA', 'DAIZ'): 'RARA',
    ('RARA', 'DAIB'): 'RARAB',
    ('RARAH', 'DAIZ'): 'RARAH',
    ('SA', 'DAIA'): 'SA',
    ('SANA', 'DAIO'): 'SANA',
    ('SANAA', 'DAIS'): 'BIBL',
    ('SC', 'DAIA'): 'SC',
    ('SEP', 'DAIB'): 'SEP',
    ('SEP', 'DAIM'): 'SEP',
    ('SI1', 'DAIA'): 'SI1',
    ('SIII2', 'DAIA'): 'SIII2',
    ('SK', 'DAIK'): 'KART',
    ('SOND', 'DAIE'): 'SEP',
    ('SOND', 'DAIF'): 'SEP',
    ('SOND', 'DAIB'): 'SOND',
    ('SONDS', 'DAIB'): 'SEP',
    ('SR01', 'DAIK'): 'SR01',
    ('SR10', 'DAIK'): 'SR10',
    ('SR11', 'DAIK'): 'SR11',
    ('SR13', 'DAIK'): 'SR13',
    ('SR14', 'DAIK'): 'SR14',
    ('SR21', 'DAIK'): 'SR21',
    ('SR23', 'DAIK'): 'SR23',
    ('SR31', 'DAIK'): 'SR31',
    ('STEA', 'DAIP'): 'EURAS',
    ('SVER', 'DAIF'): 'SVER',
    ('SVI', 'DAIA'): 'SVI',
    ('SVII', 'DAIA'): 'SVII',
    ('UG', 'DAIF'): 'UG',
    ('URUK', 'DAIO'): 'URUK',
    ('ZADAR', 'DAIF'): 'ZADAR',
    ('ZBIB', 'DAIM'): 'BIBZ'
}


def map_shelving_location(aleph_z30_collection, koha_library_code):
    if (aleph_z30_collection, koha_library_code) not in SHELVING_LOCATION_MAPPING:
        return 'UNSPECIFIED'
    else:
        return SHELVING_LOCATION_MAPPING[(aleph_z30_collection, koha_library_code)]
