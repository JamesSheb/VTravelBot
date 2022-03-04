import time
import unittest

import requests

from config_bot import HEADERS_BOT


@unittest.skip('Пропуск тестов, которые затрагивают реальный API-Hotels.')
class TestAPIHotels(unittest.TestCase):
    """
    Проверить API для поиска городов и отелей.
    """
    def setUp(self):
        self.headers = eval(HEADERS_BOT)
        self.city = 'sochi'
        self.locale = 'ru_RU'
        self.currency = 'RUB'
        self.destination_id = '10873622'

    def test_api_connection_for_city_search(self):
        """Проверить соединение с API для поиска города."""
        url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
        querystring = {'query': f'{self.city}',
                       'locale': f'{self.locale}',
                       'currency': f'{self.currency}'}

        response = requests.get(url=url,
                                headers=self.headers,
                                params=querystring)
        result = response.ok
        self.assertTrue(result)

    def test_api_connection_for_searching_hotels_with_parameters(self):
        """Проверить соединение с API для поиска отелей по параметрам."""
        time.sleep(1)
        url = "https://hotels4.p.rapidapi.com/properties/list"
        querystring = {f"destinationId": {self.destination_id},
                       "pageNumber": "1",
                       "pageSize": "25", "checkIn": "2020-01-08",
                       "checkOut": "2020-01-15", "adults1": "1",
                       f"sortOrder": 'PRICE',
                       f"locale": {self.locale},
                       f"currency": {self.currency}}

        response = requests.get(url=url,
                                headers=self.headers,
                                params=querystring)
        result = response.ok
        self.assertTrue(result)

    def test_api_connection_for_get_hotel_photo(self):
        """Проверить соединение с API для фото отелей."""
        time.sleep(1)
        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        querystring = {'id': '1505932768'}

        response = requests.get(url=url,
                                headers=self.headers,
                                params=querystring,
                                timeout=10)
        result = response.ok
        self.assertTrue(result)

    def test_expected_keys_for_city_search(self):
        """Проверить - возвращаются необходимые ключи для поиска города."""
        time.sleep(1)
        url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
        querystring = {'query': f'{self.city}',
                       'locale': f'{self.locale}',
                       'currency': f'{self.currency}'}

        response = requests.get(url=url,
                                headers=self.headers,
                                params=querystring)
        response_json = response.json()
        destinations = response_json.get('suggestions', False)[0].get(
                                                            'entities', False)
        self.assertTrue(destinations)

    def test_expected_keys_to_search_for_hotels(self):
        """
        Проверить - возвращаются необходимые ключи
         для поиска отелей по параметрам.
        """
        time.sleep(1)
        url = "https://hotels4.p.rapidapi.com/properties/list"
        querystring = {f"destinationId": {self.destination_id},
                       "pageNumber": "1",
                       "pageSize": "25", "checkIn": "2020-01-08",
                       "checkOut": "2020-01-15", "adults1": "1",
                       f"sortOrder": 'PRICE',
                       f"locale": {self.locale},
                       f"currency": {self.currency}}

        response = requests.get(url=url,
                                headers=self.headers,
                                params=querystring)
        result = response.json()
        hotels = result.get('data', False).get('body', False).get(
            'searchResults', False).get('results', False)
        self.assertTrue(hotels)

    def test_expected_keys_for_get_hotel_photo(self):
        """Проверить - возвращаются необходимые ключи для фото отеля."""
        time.sleep(1)
        number_of_photos = 1
        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        querystring = {'id': '1505932768'}

        response = requests.get(url=url,
                                headers=self.headers,
                                params=querystring,
                                timeout=10)
        response_json = response.json()
        result = response_json.get('hotelImages', False)[:number_of_photos]
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
