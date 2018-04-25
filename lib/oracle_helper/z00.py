import re

TITLE_PATTERN = re.compile('.*LKR\s\sL\$\$b(\d*)\$\$lDAI01\$\$aADM')


def get_bibliographic_id_for_adm_number(data):
    global TITLE_PATTERN
    match = TITLE_PATTERN.match(data[3])

    if match is not None:
        return match.group(1)
    return None
