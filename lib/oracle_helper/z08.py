UNIT_MAPPING = {
    'Y': 'year',
    'M': 'month',
    'W': 'week',
    'D': 'day'
}


def map_interval_type(aleph_type):
    return UNIT_MAPPING[aleph_type]
