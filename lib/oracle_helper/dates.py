# aleph: integer YYYYMMDD
# koha: date YYYY-MM-DD


def process_aleph_date(aleph_date):
    if aleph_date == 0:
        return None

    aleph_date = str(aleph_date)
    return aleph_date[0:4] + '-' + aleph_date[4:6] + '-' + aleph_date[6:]