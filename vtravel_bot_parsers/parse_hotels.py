"""
API: Hotels
https://rapidapi.com/apidojo/api/hotels4/
"""

from typing import Dict, Any, List

import requests

from config_bot import HEADERS_BOT


class ParseHotels:
    """
    Парсер отелей.
    APi: Hotels.

    Методы:
        - get_search_results_by_city: Получить результаты поиска по городу.
        - get_list_of_hotels_with_parameters: Получить список отелей
            с параметрами.
        - get_hotel_photo: Получить фото отеля.
        - collect_brief_information_about_hotels: Составить краткую информацию
            из полученных данных отелей.
    """
    def __init__(self):
        self.__headers = eval(HEADERS_BOT)
        self.__currency = 'RUB'
        self.__locale = 'ru_RU'

    def get_search_results_by_city(
                    self, city_to_search: str,) -> Dict[str, Any]:
        """
        Получить результаты поиска по городу.

        Args:
            city_to_search (str): Город для поиска.
        """
        if city_to_search.isdigit():
            raise ValueError('Введенные данные состоят из цифр.')

        url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
        querystring = {'query': f'{city_to_search}',
                       'locale': f'{self.__locale}',
                       'currency': f'{self.__currency}'}
        try:
            response = requests.get(url=url,
                                    headers=self.__headers,
                                    params=querystring,
                                    timeout=10)
            response_json = response.json()
        except Exception:
            raise ConnectionError(
                'Не удалось получить результаты поиска по городу - {0}'.format(
                    city_to_search))
        return response_json

    def get_list_of_hotels_with_parameters(
                            self, destination_id: str,
                            sort_mode: str,
                            price_min: str = None,
                            price_max: str = None,
                            distance_label: str = None) -> Dict[str, Any]:
        """
        Получить список отелей с параметрами.
        Если заданы: min price, max price - получить выборку отелей
            с заданным прайсом.
        Если задан параметр distance_to_center - получить выборку отелей
            с заданной дистанцией до центра.

        Args:
            destination_id (str): id месторасположения отелей для поиска.
            sort_mode (str): Сортировка отелей:
             sort_mode in [PRICE, PRICE_HIGHEST_FIRST, DISTANCE_FROM_LANDMARK]
                - PRICE -> сортирует от меньшей цены к большей
                - PRICE_HIGHEST_FIRST -> сортирует от большей цены к меньшей
                - DISTANCE_FROM_LANDMARK -> расстояние до центра города
            price_min (str) = None: Минимальная цена для выборки отелей.
            price_max (str) = None: Максимальная цена для выборки отелей.
            distance_label (str) = None: Метка выбора локации.
        """
        correct_modes_for_sorting = ('PRICE', 'PRICE_HIGHEST_FIRST',
                                     'DISTANCE_FROM_LANDMARK')
        if sort_mode not in correct_modes_for_sorting:
            raise ValueError(
                'Некорректный режим для сортировки отелей.'
            )

        url = "https://hotels4.p.rapidapi.com/properties/list"
        querystring = {f"destinationId": {destination_id}, "pageNumber": "1",
                       "pageSize": "25", "checkIn": "2020-01-08",
                       "checkOut": "2020-01-15", "adults1": "1",
                       f"sortOrder": {sort_mode},
                       f"locale": {self.__locale},
                       f"currency": {self.__currency}}
        if price_min:
            querystring['priceMin'] = f'{price_min}'
        if price_max:
            querystring['priceMax'] = f'{price_max}'
        if distance_label:
            querystring['landmarkIds'] = f'{distance_label}'

        try:
            response = requests.get(url=url,
                                    headers=self.__headers,
                                    params=querystring,
                                    timeout=10)
            response_json = response.json()
        except Exception:
            raise ConnectionError(
                'Не удалось получить результаты поиска по заданным параметрам')
        return response_json

    def get_hotel_photo(self, hotel_id: str,
                        number_of_photos: int) -> Dict[str, Any]:
        """
        Получить фото отеля.

        Args:
            hotel_id (int): Id отеля.
            number_of_photos (int): Необходимое количество фотографий.
        """
        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        querystring = {'id': f'{hotel_id}'}
        # querystring = {'id': '1505932768'}

        try:
            response = requests.get(url=url,
                                    headers=self.__headers,
                                    params=querystring,
                                    timeout=10)
        except Exception:
            raise ConnectionError('Не удалось получить фото отеля')

        response_json = response.json()
        try:
            result = response_json.get('hotelImages')[:number_of_photos]
        except Exception:
            raise ValueError('Ошибка поиска фотографий по ключу "hotelImages"')
        return result

    @classmethod
    def collect_brief_information_about_hotels(
                        cls, number_of_hotels: int,
                        hotels: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Составить краткую информацию из полученных данных отелей.

        Args:
            number_of_hotels (int): Количество отелей для подборки результатов.
            hotels (List[Dict[str, Any]]): Список отелей с информацией о них.
        """
        maximum_sample_result = 20
        if number_of_hotels < maximum_sample_result:
            maximum_sample_result = number_of_hotels

        selection_with_required_number_of_hotels = hotels[:maximum_sample_result]
        short_description_of_hotels = [
            {'name': hotel_info.get('name', 'no name'),
             'address': hotel_info.get('address', 'no address').get(
                                        'streetAddress', 'no address'),
             'id': hotel_info.get('id', 'no id'),
             'landmarks': hotel_info.get('landmarks')[0].get(
                 'distance', 'no distance'),
             'price': hotel_info.get('ratePlan', 'no price').get(
                 'price', 'no price').get('current', 'no price')
             }
            for hotel_info in selection_with_required_number_of_hotels
        ]
        return short_description_of_hotels

    @property
    def currency(self) -> str:
        """Получить используемую валюту."""
        return self.__currency

    @currency.setter
    def currency(self, value: str) -> None:
        """
        Установить валюту.
        Поддерживаемое значение - (USD, RUB).

        Args:
            value (str): Устанавливаемая валюта.
        """
        supported_value = ('USD', 'RUB')
        if value not in supported_value:
            raise ValueError(
                        'Неподдерживаемая валюта.\n'
                        'Доступно для установки - {0}'.format(supported_value))
        self.__currency = value

    @property
    def language_code(self) -> str:
        """Получить код языка."""
        return self.__locale

    @language_code.setter
    def language_code(self, code: str) -> None:
        """
        Установить код языка.

        Args:
            code (str): Устанавливаемый код языка.
            Поддерживаемое значение - (en_US, ru_RU).
        """
        supported_value = ('en_US', 'ru_RU')
        if code not in supported_value:
            raise ValueError(
                'Неподдерживаемый код языка.\n'
                'Доступно для установки - {0}'.format(supported_value)
            )
        self.__locale = code
