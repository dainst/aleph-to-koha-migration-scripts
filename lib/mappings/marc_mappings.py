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
