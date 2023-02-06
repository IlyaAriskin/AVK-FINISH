import math
import time
from random import randrange

from vk_api import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from config.keyboard import keyboard
from users.user import User


class VkAPI:

    def __init__(
            self,
            user_token: str,
            group_token: str,
            count: int = 10,
    ):
        self.user_api = vk_api.VkApi(token=user_token)
        self.group_api = vk_api.VkApi(token=group_token)
        self.longpoll = VkLongPoll(self.group_api)
        self.count = count

    def user_search_generator(self, request_data: dict):
        request_data.update({"count": self.count})
        request_data.update({"offset": 0})

        while True:
            result = self.user_api.method("users.search", request_data)

            # проверка результата
            if not (items := result.get('items')):
                break
            for item in items:
                yield item

            request_data['offset'] += self.count

    # Запрашиваем пол
    def get_user_sex(self, user: User):
        result = self.group_api.method("users.get", {"user_id": user.id, "fields": {"sex"}})[0]
        if 'sex' in result and result['sex'] != 0:
            return int(result['sex'])
        # запрашиваем пол
        question = "пол"
        result = self.ask_question(user, question)
        if result == "м" or result == "мужской" or result == "муж":
            return 2
        else:
            return 1

    # Проверяем, есть ли от пользователя новое сообщение и возвращаем текст сообщения
    def wait_for_answer_from_user(self) -> dict:
        for event in self.longpoll.listen():
            if event.type != VkEventType.MESSAGE_NEW or not event.to_me:
                continue
            # получаем введеный пользователем текст
            return {
                "text": event.text,
                "user_id": event.user_id
            }

    # Вывод сообщения пользователю
    def write_msg(self, user: User, message):
        self.group_api.method('messages.send', {'user_id': user.id, 'message': message, 'keyboard': keyboard,
                                                'random_id': randrange(10 ** 7), })

    # Просим ввести пользователя дополнительную информацию, если она отсутствовала:
    def ask_question(self, user: User, question) -> str:
        question_text = f"Пожалуйста, введите ваш {question}: "
        # Спрашиваем пользователя вопрос
        self.write_msg(user, question_text)
        # Читаем ответ
        answer_of_user = self.wait_for_answer_from_user()['text']
        return answer_of_user.strip().lower()

    # Достаем айди города по названию
    def get_city_id_by_title(self, title: str) -> int:
        city_id = 0
        result = self.user_api.method("database.getCities", {
            "country_id": 1,
            "q": f'{title}',
            "need_all": 0,
            "count": 1000
        })
        if result['count']:
            city_id = result['items'][0]['id']

        return city_id

    # Запрашиваем город
    def get_user_city(self, user: User) -> dict:
        city = {}
        result = self.group_api.method("users.get", {"user_id": user.id, "fields": {"city"}})[0]
        if 'city' in result:
            city = result['city']
        else:
            question = "город"
            # просим ввести название города
            city['id'] = 0
            while not city['id']:
                city_title = self.ask_question(user, question)
                city['title'] = city_title
                # достаем id города
                city['id'] = self.get_city_id_by_title(city_title)
                if not city['id']:
                    text = "Вы ввели несуществующий город. Попробуйте еще раз."
                    time.sleep(1.5)
                    self.write_msg(user, text)

        return city

    # Конвертируем дату в возраст
    @staticmethod
    def get_user_age_from_date(date_str: str) -> int:
        from datetime import datetime
        b_date = datetime.strptime(date_str, '%d.%m.%Y')
        age = math.floor((datetime.today() - b_date).days / 365)
        return age

    # Запрашиваем возраст
    def get_user_age(self, user: User):
        result = self.group_api.method("users.get", {"user_id": user.id, "fields": {"bdate"}})[0]
        if 'bdate' in result and len(result['bdate']) > 5:
            age = VkAPI.get_user_age_from_date(date_str=result['bdate'])
            return age
        else:
            result = ""
            while not result.isdigit():
                result = self.ask_question(user, "возраст")
            return result

    # Получить фотографию людей для знакомства

    def get_photos_of_person(self, person_id):
        request = {
            "type": "album",
            "owner_id": person_id,
            "extended": 1,
            "count": 25,
            "skip_hidden": 1
        }
        photos = self.user_api.method("photos.getAll", request)['items']
        # Сортировка по количеству лайков
        photos = sorted(photos, key=lambda d: d['likes']['count'], reverse=True)
        return photos
