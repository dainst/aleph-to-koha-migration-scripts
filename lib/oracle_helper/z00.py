import re

TITLE_PATTERN = re.compile('.*LKR\s\sL\$\$b(\d{9})\$\$lDAI01\$\$aADM.*')
TITLE_PATTERN_2 = re.compile('.*LKR\s\sL\$\$b(\d{9})\$\$aADM\$\$lDAI01.*')
TITLE_PATTERN_3 = re.compile('.*LKR\s\sL\$\$lDAI01\$\$b(\d{9})\$\$aADM.*')
TITLE_PATTERN_4 = re.compile('.*LKR\s\sL\$\$\aADM$\$b(\d{9})\$\$lDAI01.*')
TITLE_PATTERN_5 = re.compile('.*LKR\s\sL\$\$lDAI01\$\$aADM\$\$b(\d{9}).*')
TITLE_PATTERN_6 = re.compile('.*LKR\s\sL\$\$aADM\$\$lDAI01\$\$b(\d{9}).*')


def get_bibliographic_id_for_adm_number(data):
    global TITLE_PATTERN
    match = TITLE_PATTERN.match(data[3])
    if match is not None:
        return match.group(1)
    match = TITLE_PATTERN_2.match(data[3])
    if match is not None:
        return match.group(1)
    match = TITLE_PATTERN_3.match(data[3])
    if match is not None:
        return match.group(1)
    match = TITLE_PATTERN_4.match(data[3])
    if match is not None:
        return match.group(1)
    match = TITLE_PATTERN_5.match(data[3])
    if match is not None:
        return match.group(1)
    match = TITLE_PATTERN_6.match(data[3])
    if match is not None:
        return match.group(1)
    return None
