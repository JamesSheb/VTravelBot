"""
API: Deep Translate
https://rapidapi.com/gatzuma/api/deep-translate1/
"""

import json

import requests

from config_bot import HEADERS_TRANSLATOR


class TextTranslator:
    """
    Переводчик текста.

    Методы:
        - supported_languages: Получить поддерживаемые языки.
        - translate: Перевести заданный текст.
    """
    def __init__(self):
        self.__headers = eval(HEADERS_TRANSLATOR)
        self.__text_language = 'ru'
        self.__target_language = 'en'

    def supported_languages(self) -> 'requests.Response.json':
        """Узнать о поддерживаемых языках."""
        url = "https://deep-translate1.p.rapidapi.com/language/translate/v2/languages"

        try:
            response = requests.get(url, headers=self.__headers)
            response_json = response.json()
        except Exception as error_message:
            raise ConnectionError('Не удалось получить данные.\n{0}'.format(
                error_message
            ))
        return response_json

    def translate(self, text: str) -> str:
        """
        Перевести текст.

        Сделать запрос POST и предоставить JSON в теле запроса,
        который определяет язык для перевода (target)
        и текст для перевода (q).

        Args:
            text (str): Текст для перевода.

        Raises:
            ConnectionError: Если не удалось получить данные от API.
            ValueError: Если не удалось получить переводимый текст по ключам.
        """
        url = "https://deep-translate1.p.rapidapi.com/language/translate/v2"
        payload = json.dumps({
            'q': text,
            'source': self.__text_language,
            'target': self.__target_language
        })
        try:
            response = requests.post(url, data=payload, headers=self.__headers)
            response_json = response.json()
        except Exception as error_message:
            raise ConnectionError('Не удалось получить данные.\n{0}'.format(
                error_message
            ))

        try:
            translated_text = response_json[
                                    'data']['translations']['translatedText']
        except Exception as error_message:
            raise ValueError(
                'Не удалось получить переводимый текст по ключам\n{0}'.format(
                    error_message
                ))
        return translated_text

    @property
    def text_language(self) -> str:
        """Получить язык переводимого текста."""
        return self.__text_language

    @text_language.setter
    def text_language(self, language: str) -> None:
        """
        Установить язык переводимого текста.

        Узнать поддерживаемые языки - метод supported_languages.
        """
        self.__text_language = language

    @property
    def target_language(self) -> str:
        """Получить язык перевода."""
        return self.__target_language

    @target_language.setter
    def target_language(self, language: str) -> None:
        """
        Установить язык перевода.

        Узнать поддерживаемые языки - метод supported_languages.
        """
        self.__target_language = language

    def __str__(self) -> str:
        """Вернуть описание класса с языками: переводимого текста, перевода."""
        description = ('Переводчик текста.\n\n'
                       'Язык переводимого текста: {0}\n'
                       'Язык перевода: {1}'.format(self.__text_language,
                                                   self.__target_language))
        return description
