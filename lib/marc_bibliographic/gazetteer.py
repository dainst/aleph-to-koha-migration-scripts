import logging

import requests

from typing import Dict


class GazetteerThesaurusMapper:
    _query: str = '{"bool":{"must":[{"nested":{"path":"ids","query":{"match":{"ids.context":"zenon-thesaurus"}}}}]}}'
    _url: str = 'https://gazetteer.dainst.org/search.json'
    _payload: Dict[str, str] = {'limit': '100000',
                                'noPolygons': 'true',
                                'q': _query,
                                'type': 'extended'}
    mapping = dict()

    def fetch_data(self):
        response: requests.Response = None
        json_data = None

        try:
            response: requests.Response = requests.get(url=self._url, params=self._payload)
            response.raise_for_status()
            json_data = response.json()

        except ValueError:
            self.logger.error('JSON decoding fails!\n' + response.text)

        except requests.exceptions.RequestException as exception:
            self.logger.error(f'Gazetteer service request fails!'
                              f'\nRequest: {exception.request}'
                              f'\nResponse: {exception.response}')

        return json_data

    def __init__(self, logger=None):

        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info('Initializing, loading data and creating mapping...')

        data: dict = self.fetch_data()

        for place in data['result']:
            for identifier in place['identifiers']:
                if identifier['context'] == 'zenon-thesaurus':
                    self.mapping[identifier['value']] = place['gazId']

        self.logger.info('Initialization done.')


if __name__ == '__main__':
    gazetteer = GazetteerThesaurusMapper()

