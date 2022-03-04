import os
import string
from typing import Dict, List, Any

import telebot
from telebot import types
from loguru import logger

from config_bot import BOT_TOKEN
from vtravel_bot_parsers import ParseHotels
from vtravel_bot_parsers import TextTranslator


logger.add(
    'logs/bot.log',
    format="{time:YYYY-MM-DD at HH:mm:ss} {file} (line -{line})  {level}  {message} <- {function}",
    level='DEBUG',
    rotation='1 week',
    retention=4,
    compression='zip'
)

bot = None
try:
    bot = telebot.TeleBot(token=BOT_TOKEN)
except Exception as bot_error:
    logger.exception(bot_error)


@bot.message_handler(commands=['start'])
@logger.catch
def start_bot(message: types.Message) -> None:
    """Запустить бота приветствием и стикером."""
    try:
        path_to_sticker = os.path.abspath(
            os.path.join('', 'static/stickers/HelloAnimatedSticker.tgs'))
        sticker = open(path_to_sticker, mode='rb')
    except FileNotFoundError:
        sticker = '👋'
    hello_messages = 'Привет!\nЯ бот турагенства.\n' \
                     'Помогу подобрать самые лучшие отели для вас!\n\n'

    try:
        bot.send_sticker(message.chat.id, sticker)
    except Exception as error_message:
        logger.exception('Ошибка загрузки стикера "hello" - {0}'.format(
                                                                error_message))
        bot.send_message(message.chat.id, sticker)

    bot.send_message(message.chat.id, hello_messages)

    markup = create_command_buttons()
    buttons_message = 'Нажмите на более предпочтительный выбор'
    bot.send_message(message.chat.id, buttons_message, reply_markup=markup)


@logger.catch
def create_command_buttons() -> 'types.InlineKeyboardMarkup':
    """
    Создать кнопки для команд:
        [lowprice, highprice, bestdeal, history, help]
    """
    markup = types.InlineKeyboardMarkup(row_width=1)

    lowprice_button = types.InlineKeyboardButton(
                                            'Топ дешёвых отелей',
                                            callback_data='lowprice_button')
    high_button = types.InlineKeyboardButton('Топ дорогих отелей',
                                             callback_data='high_button')
    bestdeal_button = types.InlineKeyboardButton(
                                            'Топ отелей, подходящих по цене',
                                            callback_data='bestdeal_button')
    # history_button = types.InlineKeyboardButton(
    #                                     'История поиска отелей',
    #                                     callback_data='history_button')
    help_button = types.InlineKeyboardButton(
                                            'Помощь по командам',
                                            callback_data='help_button')

    markup.add(lowprice_button, high_button, bestdeal_button, help_button)
    return markup


@bot.callback_query_handler(func=lambda call: call.data == 'help_button')
@logger.catch()
def callback_send_description_of_all_commands(
                                            call: types.CallbackQuery) -> None:
    """
    Ответить на нажатие кнопки help_button.
    Отправить описание команд.
    """
    command_description = command_all_description()
    bot.send_message(call.message.chat.id, command_description)


@bot.message_handler(commands=['help'])
def reply_to_help_command(message: types.Message) -> None:
    """
    Ответить на нажатие команды - /help.
    Отправить описание команд.
    """
    command_description = command_all_description()
    bot.send_message(message.chat.id, command_description)


def command_all_description() -> str:
    """
    Отправить описание команд:
        [lowprice, highprice, bestdeal, history]
    """
    command_description = (
        "/lowprice - Узнать топ самых дешёвых отелей в городе\n"
        "/highprice - Узнать топ самых дорогих отелей в городе\n"
        "/bestdeal - Узнать топ отелей, наиболее подходящих по цене"
        " и расположению от центра\n"
        "/history - Узнать историю поиска отелей\n"
    )
    return command_description


@bot.callback_query_handler(
    func=lambda call: call.data in (
                        'lowprice_button', 'high_button', 'bestdeal_button'))
def callback_user_selection_button(call: types.CallbackQuery) -> None:
    """Обработать нажатие кнопок: [lowprice, highprice, bestdeal]."""
    buttons_and_modes = {
        'lowprice_button': 'PRICE',
        'high_button': 'PRICE_HIGHEST_FIRST',
        'bestdeal_button': 'DISTANCE_FROM_LANDMARK'
    }
    mode_for_sorting = buttons_and_modes.get(call.data)
    logger.debug('Выбор пользователя - кнопка {0}'.format(call.data))
    city_selection = bot.send_message(call.message.chat.id,
                                      'Введите город для поиска:')

    if mode_for_sorting == 'DISTANCE_FROM_LANDMARK':
        bot.register_next_step_handler(city_selection,
                                       get_lowest_hotel_price,
                                       mode_for_sorting)
    else:
        bot.register_next_step_handler(city_selection,
                                       city_search,
                                       mode_for_sorting)


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
@logger.catch
def command_user_choice_command(message: types.Message) -> None:
    """Обработать команды: [lowprice, highprice, bestdeal]"""
    commands_and_modes = {
        '/lowprice': 'PRICE',
        '/highprice': 'PRICE_HIGHEST_FIRST',
        '/bestdeal': 'DISTANCE_FROM_LANDMARK'
    }
    mode_for_sorting = commands_and_modes.get(message.text)
    logger.debug('Выбор пользователя - команда {0}'.format(message.text))
    city_selection = bot.send_message(message.chat.id,
                                      'Введите город для поиска:')

    if mode_for_sorting == 'DISTANCE_FROM_LANDMARK':
        bot.register_next_step_handler(city_selection,
                                       get_lowest_hotel_price,
                                       mode_for_sorting)
    else:
        bot.register_next_step_handler(city_selection,
                                       city_search,
                                       mode_for_sorting)


@logger.catch
def get_lowest_hotel_price(message: types.Message,
                           mode_for_sorting: str) -> None:
    """
    Получить от пользователя минимальную цену за отель.

    Args:
        message (types.Message): Ответ от пользователя - город для поиска.
        mode_for_sorting (str): Режим сортировки поиска отелей.
    """
    search_city = message
    minimum_price = bot.send_message(message.chat.id,
                                     'Введите цифрами минимальную цену отеля:')
    bot.register_next_step_handler(minimum_price,
                                   get_highest_hotel_price,
                                   search_city,
                                   mode_for_sorting)


@logger.catch
def get_highest_hotel_price(message: types.Message,
                            search_city: types.Message,
                            mode_for_sorting: str) -> None:
    """
    Получить от пользователя максимальную цену за отель.

    Args:
        message (types.Message): Ответ от пользователя - минимальная цена.
        search_city (types.Message): Ответ от пользователя - город для поиска.
        mode_for_sorting (str): Режим сортировки поиска отелей.
    """
    minimum_price = None
    logger.info(
        'Минимальная цена за отель, выбранная пользователем {0}'.format(
                                                                message.text))
    try:
        minimum_price = int(message.text)
    except Exception as error_message:
        logger.warning(
            'Ошибка ввода пользователем: {0}'
            'Введенная пользователем минимальная цена: {1}'.format(
                                                error_message, message.text)
        )
        price = bot.send_message(message.chat.id,
                                 'Введите минимальную цену - цифрами:')
        bot.register_next_step_handler(price,
                                       get_highest_hotel_price,
                                       search_city,
                                       mode_for_sorting)

    if minimum_price:
        maximum_price = bot.send_message(
                                    message.chat.id,
                                    'Введите цифрами максимальную цену отеля:')
        bot.register_next_step_handler(maximum_price,
                                       get_complete_information_on_bestdeal,
                                       search_city,
                                       mode_for_sorting,
                                       minimum_price)


@logger.catch
def get_complete_information_on_bestdeal(message: types.Message,
                                         search_city: types.Message,
                                         mode_for_sorting: str,
                                         minimum_price: int) -> None:
    """
    Получить полную информацию по поиску отелей в режиме bestdeal.

    Args:
        message (types.Message): Ответ от пользователя - максимальная цена.
        search_city (types.Message): Ответ от пользователя - город для поиска.
        mode_for_sorting (str): Режим сортировки поиска отелей.
        minimum_price (int): Минимальная цена для поиска отелей.
    """
    maximum_price = None
    logger.info(
        'Максимальная цена за отель, выбранная пользователем {0}'.format(
                                                                message.text))
    try:
        maximum_price = int(message.text)
    except Exception as error_message:
        logger.warning(
            'Ошибка ввода пользователем: {0}'
            'Введенная пользователем максимальная цена: {1}'.format(
                                                error_message, message.text)
        )
        price = bot.send_message(message.chat.id,
                                 'Введите максимальную цену - цифрами:')
        bot.register_next_step_handler(price,
                                       get_complete_information_on_bestdeal,
                                       search_city,
                                       mode_for_sorting,
                                       minimum_price)

    if maximum_price:
        bestdeal = [minimum_price, maximum_price]
        city_search(search_city,
                    mode_for_sorting,
                    bestdeal)


@logger.catch
def translation_of_text_from_russian_into_english(city_name: str) -> str:
    """
    Проверить, если город буквами (ru) - меняем на (en).
    Если ошибка в переводе, возвращаем название города на (en).

    Args:
        city_name (str): Название города.
    """
    if any(map(
            lambda letter: letter not in string.ascii_letters, city_name)):
        translator = TextTranslator()
        logger.info(
            'Город введен кириллицей: {0},'
            ' выполняется перевод с (ru) -> (en)'.format(city_name))
        try:
            city_name = translator.translate(text=city_name)
        except (ConnectionError, ValueError) as error_message:
            logger.error(error_message)

    logger.info(
        'Выбранный город пользователем для поиска: {0}'.format(city_name))
    return city_name


@logger.catch
def city_search(message: types.Message, mode_for_sorting: str,
                bestdeal_mode: List[int] = None) -> None:
    """
    Поиск отелей по выбранному городу от пользователя.
    Найти возможные направления города.

    Args:
        message: types.Message
        mode_for_sorting (str): Режим сортировки поиска отелей.
        bestdeal_mode (List[int]) = None: Если задан данный параметр
            в списке передается [минимальная цена отеля,
                                максимальная цена отеля]
    """
    temporary_message = bot.send_message(message.chat.id,
                                         'Ожидайте загрузки...')

    selected_city_to_search = translation_of_text_from_russian_into_english(
        city_name=message.text
    )
    search_results = None
    try:
        parser = ParseHotels()
        search_results = parser.get_search_results_by_city(
                                        city_to_search=selected_city_to_search)
    except ConnectionError as error_message:
        logger.error(error_message)
        bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=temporary_message.id,
                        text='Ошибка поиска, попробуйте пожалуйста еще раз')
    except ValueError as error_message:
        logger.error(error_message)
        city = bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=temporary_message.id,
                        text='Введите город буквами')
        bot.register_next_step_handler(city, city_search, mode_for_sorting)

    if search_results:
        try:
            destinations = search_results.get('suggestions')[0].get('entities')
            found_destinations = {
                destination.get('caption'): destination.get('destinationId')
                for destination in destinations
                }

            if not bestdeal_mode:
                markup = create_buttons_to_select_destination(
                                                        found_destinations,
                                                        mode_for_sorting)
            else:
                markup = create_buttons_to_select_destination(
                                                        found_destinations,
                                                        mode_for_sorting,
                                                        bestdeal_mode
                )

            bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=temporary_message.id,
                        text='Выберите месторасположение для поиска отелей',
                        reply_markup=markup)
        except Exception as error_message:
            logger.exception(error_message)
            bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=temporary_message.id,
                        text='Ошибка поиска, попробуйте пожалуйста еще раз')


@logger.catch
def create_buttons_to_select_destination(
            destinations: Dict[str, str],
            mode_for_sorting: str,
            bestdeal_mode: List[int] = None) -> 'types.InlineKeyboardMarkup':
    """
    Создать кнопки для выбора пункта назначения поиска отелей.

    callback_data - состоит из 3-х частей, если bestdeal_mode = None:
        - слово: destinationId
        - id: id месторасположения
        - режим сортировки отелей

    callback_data - состоит из 5-ти частей, если bestdeal_mode:
        Добавляется к первым 3 частям:
            - минимальная цена отеля
            - максимальная цена отеля

    Args:
       destinations (Dict[str, str]): Найденные направления.
       mode_for_sorting (str): Режим сортировки поиска отелей.
       bestdeal_mode (List[int]) = None: Если задан данный параметр
            в списке передается [минимальная цена отеля,
                                максимальная цена отеля]
    """
    markup = types.InlineKeyboardMarkup()

    for destination_name, destination_id in destinations.items():
        callback_data = f'destinationId-{destination_id}-{mode_for_sorting}'
        if bestdeal_mode:
            callback_data = f'destinationId-{destination_id}-' \
                            f'{mode_for_sorting}-{bestdeal_mode[0]}-' \
                            f'{bestdeal_mode[1]}'
        button = types.InlineKeyboardButton(
            destination_name,
            callback_data=callback_data
        )
        markup.add(button)

    return markup


@bot.callback_query_handler(
    func=lambda call: call.data.split('-')[0] == 'destinationId')
@logger.catch
def hotel_search(call: types.CallbackQuery):
    """
    Поиск отелей.

    В callback - передается строка с параметрами для поиска отелей:
        Вид строки:
            'destinationId-{destination_id}-{mode_for_sorting}'
        или
            'destinationId-{destination_id}-{mode_for_sorting}-{min price}-{max price}'

    Args:
        call (types.CallbackQuery):
            Содержит информацию:
                строка destinationId - id для поиска - режим сортировки отелей
                - минимальная цена - максимальная цена
    """
    temporary_message = bot.send_message(
        call.message.chat.id, 'Ожидайте загрузки...')

    information_about_hotel_search = call.data.split('-')
    destination_search_id = information_about_hotel_search[1]
    hotel_search_mode = information_about_hotel_search[2]

    search_results = None
    try:
        parser = ParseHotels()
        if len(information_about_hotel_search) == 3:
            search_results = parser.get_list_of_hotels_with_parameters(
                destination_id=destination_search_id,
                sort_mode=hotel_search_mode
            )
        else:
            distance_label = 'City center'
            search_results = parser.get_list_of_hotels_with_parameters(
                destination_id=destination_search_id,
                sort_mode=hotel_search_mode,
                price_min=information_about_hotel_search[3],
                price_max=information_about_hotel_search[4],
                distance_label=distance_label
            )
    except ConnectionError as error_message:
        logger.error(error_message)
        bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=temporary_message.id,
                    text='Не удалось получить результаты поиска по заданным '
                         'параметрам\nПопробуйте пожалуйста еще раз')
    except ValueError as error_message:
        logger.error(error_message)
        bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=temporary_message.id,
                    text='Ошибка поиска, попробуйте пожалуйста еще раз')

    if search_results:
        hotels = None
        try:
            hotels = search_results.get('data').get('body').get(
                'searchResults').get('results')
        except Exception as error_message:
            logger.exception(error_message)
            bot.send_message(call.message.chat.id,
                             'Ошибка поиска, попробуйте пожалуйста еще раз')

        if hotels:
            number_of_hotels = bot.edit_message_text(
                message_id=temporary_message.id,
                chat_id=call.message.chat.id,
                text='Введите количество отелей для вывода результатов\n'
                'От 1 до 20 (включительно)')
            bot.register_next_step_handler(number_of_hotels,
                                           get_number_of_hotels_from_user,
                                           hotels)


@logger.catch
def get_number_of_hotels_from_user(message: types.Message,
                                   hotels: List[Dict[str, Any]]) -> None:
    """
    Получить от пользователя количество отелей.

    Args:
        message: types.Message
        hotels (List[Dict[str, Any]]): Список отелей с информацией о них.
    """
    number_of_hotels = None
    logger.info('Введенное количество отелей от пользователя = {0}'.format(
                                                                message.text))
    try:
        number_of_hotels = int(message.text)
    except ValueError as error_message:
        logger.exception('Ошибка ввода от пользователя - {0}'.format(
                                                                error_message))
        chat_message = bot.send_message(
                                message.chat.id,
                                'Введите пожалуйста цифрами.')
        bot.register_next_step_handler(chat_message,
                                       get_number_of_hotels_from_user)

    if number_of_hotels:
        if number_of_hotels < 1:
            logger.warning(
                'Пользователь ввел количество ожидаемых'
                ' результатов {0} < 1'.format(number_of_hotels)
            )
            chat_message = bot.send_message(
                                message.chat.id,
                                'Введите количество от 1 до 20 (включительно)')
            bot.register_next_step_handler(chat_message,
                                           get_number_of_hotels_from_user)
        else:
            photo = bot.send_message(
                message.chat.id,
                'Необходимо ли загрузить фотографии отеля (да/нет) ?')
            bot.register_next_step_handler(photo,
                                           photo_upload,
                                           number_of_hotels,
                                           hotels)


@logger.catch
def photo_upload(message: types.Message, number_of_hotels: int,
                 hotels: List[Dict[str, Any]]) -> None:
    """
    Получить от пользователя ответ - необходимо ли загружать фото отеля.
        Если да - необходимое количество фотографий.

    Args:
        message: types.Message
        number_of_hotels (int): Количество отелей для подборки результатов.
        hotels (List[Dict[str, Any]]): Список отелей с информацией о них.
    """
    photo = True if message.text.lower() == 'да' else False

    if photo:
        number_photos = bot.send_message(
            message.chat.id,
            'Введите цифрами количество фотографий от 1 до 5 (включительно)')
        bot.register_next_step_handler(
            number_photos,
            get_selection_of_hotels,
            number_of_hotels,
            hotels
        )
    else:
        logger.info('Выбрана загрузка отелей без фото')
        get_selection_of_hotels(message,
                                number_of_hotels=number_of_hotels,
                                hotels=hotels)


@logger.catch
def get_selection_of_hotels(message: types.Message, number_of_hotels: int,
                            hotels: List[Dict[str, Any]]) -> None:
    """
    Получить подборку подборку с заданным количеством отелей.

    Args:
        message: types.Message
        number_of_hotels (int): Количество отелей для подборки результатов.
        hotels (List[Dict[str, Any]]): Список отелей с информацией о них.
    """
    try:
        number_of_photos = int(message.text)
    except Exception as error_message:
        logger.error(error_message)
        logger.warning(
            'Необходимое количество фотографий '
            'от пользователя = {0}'.format(message.text)
        )
        number_of_photos = 5
    logger.info(
        'Количество фото от пользователя для загрузки = {0}'.format(
                                                        number_of_photos))

    logger.info('Получить подборку отелей (количество = {0})'.format(
                                                            number_of_hotels))
    parser = ParseHotels()
    selection_of_hotels = None
    try:
        selection_of_hotels = parser.collect_brief_information_about_hotels(
                                            number_of_hotels=number_of_hotels,
                                            hotels=hotels)
    except Exception as error_message:
        logger.exception(error_message)
        bot.send_message(message.chat.id,
                         'Ошибка поиска, попробуйте пожалуйста еще раз')

    if number_of_photos and selection_of_hotels:
        if number_of_photos not in range(1, 5):
            number_of_photos = 5
        send_information_about_found_hotels(
                                        message,
                                        selected_hotels=selection_of_hotels,
                                        number_of_photos=number_of_photos)
    else:
        send_information_about_found_hotels(
                                        message,
                                        selected_hotels=selection_of_hotels)


@logger.catch
def send_information_about_found_hotels(message: types.Message,
                                        selected_hotels: List[Dict[str, str]],
                                        number_of_photos: int = None) -> None:
    """
    Отправить пользователю информацию о найденных отелях.
    Если пользователь выбрал загрузку фотографий - вывести необходимое
        количество фотографий отеля.

    Args:
        message: types.Message
        selected_hotels (List[Dict[str, str]]): Подборка отелей.
        number_of_photos (int) = None: Количество загружаемых фотографий.
    """
    logger.info('Отправить пользователю информацию о найденных отелях')
    parser = ParseHotels()
    bot.send_message(message.chat.id, 'Подборка отелей:')
    for hotel in selected_hotels:
        short_description = (
            '🏨\n'
            'Название отеля: {name}\n'
            'Адрес отеля: {address}\n'
            'Расположение от центра: {landmarks}\n'
            'Цена: {price}'.format(
                name=hotel.get('name'),
                address=hotel.get('address'),
                landmarks=hotel.get('landmarks'),
                price=hotel.get('price')
            )
        )
        bot.send_message(message.chat.id, short_description)

        if number_of_photos:
            temporary_message = bot.send_message(message.chat.id,
                                                 'Загрузка фото...')
            try:
                hotel_photos = parser.get_hotel_photo(
                                        hotel_id=hotel.get('id'),
                                        number_of_photos=number_of_photos)
                for number, photo in enumerate(hotel_photos, 1):
                    logger.info('Загрузка {0} фотографии. Отель - {1}'.format(
                        number,
                        hotel.get('name')
                    ))
                    image_url = photo.get('baseUrl').format(size='y')
                    bot.send_photo(message.chat.id, image_url)
                bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=temporary_message.id,
                        text='Фото отеля:')
            except (ConnectionError, ValueError) as error_message:
                logger.warning(error_message)
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=temporary_message.id,
                    text='Не удалось загрузить фото отеля'
                )


@bot.message_handler(content_types=['text'])
@logger.catch
def process_all_messages_from_user(message: types.Message) -> None:
    """
    Обработать сообщения от пользователя и перенаправить на "/" или "/help".
    """
    if message.text:
        logger.info('Неизвестный ввод от пользователя.')
        bot.send_message(
                        chat_id=message.chat.id,
                        text='Введите символ - "/" или "/help" для просмотра '
                             'всех команд.')


if __name__ == '__main__':
    try:
        logger.debug('Start bot')
        bot.polling(none_stop=True, interval=0)
    except Exception as error:
        logger.exception(error)
