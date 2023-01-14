import math
import time
from random import randrange

from vk_api import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from config.keyboard import keyboard
from config.settings import user_token
from users.user import User


class VkAPI:
    # Запрашиваем пол
    @staticmethod
    def get_user_sex(user: User, vk):
        result = vk.method("users.get", {"user_id": user.id, "fields": {"sex"}})[0]
        if 'sex' in result and result['sex'] != 0:
            return int(result['sex'])
        # запрашиваем пол
        question = "пол"
        result = VkAPI.ask_question(user, question, vk)
        if result == "м" or result == "мужской" or result == "муж":
            return 2
        else:
            return 1

    # Проверяем, есть ли от пользователя новое сообщение и возвращаем текст сообщения
    @staticmethod
    def wait_for_answer_from_user(longpoll) -> dict:
        for event in longpoll.listen():
            if event.type != VkEventType.MESSAGE_NEW or not event.to_me:
                continue
            # получаем введеный пользователем текст
            return {
                "text": event.text,
                "user_id": event.user_id
            }

    # Вывод сообщения пользователю
    @staticmethod
    def write_msg(user: User, message, vk):
        vk.method('messages.send', {'user_id': user.id, 'message': message, 'keyboard': keyboard, 'random_id': randrange(10 ** 7), })

    # Просим ввести пользователя дополнительную информацию, если она отсутствовала:
    @staticmethod
    def ask_question(user: User, question, vk) -> str:
        longpoll = VkLongPoll(vk)
        question_text = f"Пожалуйста, введите ваш {question}: "
        # Спрашиваем пользователя вопрос
        VkAPI.write_msg(user, question_text, vk)
        # Читаем ответ
        answer_of_user = VkAPI.wait_for_answer_from_user(longpoll)['text']
        return answer_of_user.strip().lower()

    # Достаем айди города по названию
    @staticmethod
    def get_city_id_by_title(title: str) -> int:
        vk_api_with_person_token = vk_api.VkApi(token=user_token)
        city_id = 0
        result = vk_api_with_person_token.method("database.getCities", {
            "country_id": 1,
            "q": f'{title}',
            "need_all": 0,
            "count": 1000
        })
        if result['count']:
            city_id = result['items'][0]['id']

        return city_id

    # Запрашиваем город
    @staticmethod
    def get_user_city(user: User, vk) -> dict:
        city = {}
        result = vk.method("users.get", {"user_id": user.id, "fields": {"city"}})[0]
        if 'city' in result:
            city = result['city']
        else:
            question = "город"
            # просим ввести название города
            city['id'] = 0
            while not city['id']:
                city_title = VkAPI.ask_question(user, question, vk)
                city['title'] = city_title
                # достаем id города
                city['id'] = VkAPI.get_city_id_by_title(city_title)
                if not city['id']:
                    text = "Вы ввели несуществующий город. Попробуйте еще раз."
                    time.sleep(1.5)
                    VkAPI.write_msg(user, text, vk)

        return city

    # Конвертируем дату в возраст
    @staticmethod
    def get_user_age_from_date(date_str: str) -> int:
        from datetime import datetime
        b_date = datetime.strptime(date_str, '%d.%m.%Y')
        age = math.floor((datetime.today() - b_date).days / 365)
        return age

    # Запрашиваем возраст
    @staticmethod
    def get_user_age(user: User, vk):
        result = vk.method("users.get", {"user_id": user.id, "fields": {"bdate"}})[0]
        if 'bdate' in result and len(result['bdate']) > 5:
            age = VkAPI.get_user_age_from_date(date_str=result['bdate'])
            return age
        else:
            result = ""
            while not result.isdigit():
                result = VkAPI.ask_question(user, "возраст", vk)
            return result

    # Получить фотографию людей для знакомства
    @staticmethod
    def get_photos_of_person(person_id, vk_api_user_token):
        request = {
            "type": "album",
            "owner_id": person_id,
            "extended": 1,
            "count": 25,
            "skip_hidden": 1
        }
        photos = vk_api_user_token.method("photos.getAll", request)['items']
        # Сортировка по количеству лайков
        photos = sorted(photos, key=lambda d: d['likes']['count'], reverse=True)
        return photos
