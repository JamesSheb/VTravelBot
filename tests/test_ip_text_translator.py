import unittest
import json
import time

import requests

from config_bot import HEADERS_TRANSLATOR


@unittest.skip('Пропуск тестов, которые затрагивают реальный API-Translator.')
class TestTextTranslator(unittest.TestCase):
    """
    Проверить API для перевода текста.
    """
    def setUp(self):
        self.headers = eval(HEADERS_TRANSLATOR)
        self.payload = json.dumps({
            'q': 'Сочи',
            'source': 'ru',
            'target': 'en'
        })

    def test_api_connection_for_supported_languages(self):
        """Проверить соединение с API для поддерживаемых языков."""
        url = "https://deep-translate1.p.rapidapi.com/language/translate/v2/languages"

        response = requests.get(url, headers=self.headers)
        result = response.ok
        self.assertTrue(result)

    def test_api_connection_for_text_translation(self):
        """Проверить соединение с API для перевода текста."""
        time.sleep(1)
        url = "https://deep-translate1.p.rapidapi.com/language/translate/v2"

        response = requests.post(url, data=self.payload, headers=self.headers)
        result = response.ok
        self.assertTrue(result)

    def test_expected_keys_for_text_translation(self):
        """Проверить - возвращаются необходимые ключи для перевода текста."""
        time.sleep(1)
        url = "https://deep-translate1.p.rapidapi.com/language/translate/v2"

        response = requests.post(url, data=self.payload, headers=self.headers)
        response_json = response.json()
        translated_text = response_json.get('data', False).get(
            'translations', False).get('translatedText', False)
        self.assertTrue(translated_text)


if __name__ == '__main__':
    unittest.main()
