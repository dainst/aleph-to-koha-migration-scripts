import logging

import requests

from typing import Dict


class GazetteerThesaurusMapper:
    _query: str = '{"bool":{"must":[{"nested":{"path":"ids","query":{"match":{"ids.context":"zenon-thesaurus"}}}}]}}'
    _url: str = 'https://gazetteer.dainst.org/search.json'
    _payload: Dict[str, str] = {'noPolygons': 'true',
                                'q': _query,
                                'type': 'extended',
                                'limit': 1000}
    mapping = dict()

    def fetch_batch(self, scroll_id):
        try:
            response: requests.Response = requests.get(
                url=self._url, params={**self._payload, **{'scrollId': scroll_id}}
            )
            response.raise_for_status()
            json_data = response.json()
            return json_data['result']

        except ValueError:
            self.logger.error('JSON decoding fails!\n' + response.text)

        except requests.exceptions.RequestException as exception:
            self.logger.error(f'Gazetteer service request fails!'
                              f'\nRequest: {exception.request}'
                              f'\nResponse: {exception.response}')

        return []

    def fetch_data(self):
        response: requests.Response = None
        scroll_id = None

        results = []

        try:
            response: requests.Response = requests.get(
                url=self._url, params={**self._payload, **{'scroll': 'true'}}
            )
            response.raise_for_status()
            json_data = response.json()
            results = json_data['result']
            scroll_id = json_data['scrollId']

            self.logger.info(f'{json_data["total"]} places found.')

        except ValueError:
            self.logger.error('JSON decoding fails!\n' + response.text)

        except requests.exceptions.RequestException as exception:
            self.logger.error(f'Gazetteer service request fails!'
                              f'\nRequest: {exception.request}'
                              f'\nResponse: {exception.response}')

        next_batch = self.fetch_batch(scroll_id)
        results += next_batch
        while next_batch:
            next_batch = self.fetch_batch(scroll_id)
            results += next_batch

        return results

    def __init__(self, logger=None):

        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info('Initializing, loading data and creating mapping...')

        results: dict = self.fetch_data()

        for place in results:
            for identifier in place['identifiers']:
                if identifier['context'] == 'zenon-thesaurus':
                    self.mapping[identifier['value']] = place['gazId']

        self.logger.info('Initialization done.')


if __name__ == '__main__':
    gazetteer = GazetteerThesaurusMapper()

