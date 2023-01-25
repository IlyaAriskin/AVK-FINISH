import time
from datetime import datetime
from random import randrange

import vk_api
from vk_api.longpoll import VkLongPoll
from database.database import *
from api.vkontake import VkAPI

#экономить так экономить
def user_search_generator(request_data: dict, vk_api_with_person_token: vk_api.VkApi):
    request_data.update({"count": 10})
    request_data.update({"offset": 0})

    while True:
        result = vk_api_with_person_token.method("users.search", request_data)
        for item in result['items']:
            yield item
        request_data['offset'] += 10

# Осуществляем поиск партнера, находим самые популярные фотографии и возвращаем их пользователю
def search_sex_partner(user: User, vk_api_with_group_token):
    vk_api_with_person_token = vk_api.VkApi(token=user_token)
    # Получаем список пользователей
    request_data = set_search_parameters(user)

    # Показываем пользователю найденных половых партнеров
    text = f"Поиск закончен!\n\n Приступаю к показу анкет."
    VkAPI.write_msg(user, text, vk_api_with_group_token)
    time.sleep(2)

    i = 0
    for data in user_search_generator(request_data, vk_api_with_person_token):
        # Проверяем, показывали ли этого партнера его ранее
        if not db_check_is_new_partner(user.id, data['id']):
            continue
        # Получаем фотографии
        try:
            photos = VkAPI.get_photos_of_person(data['id'], vk_api_with_person_token)
            main_photo_url = photos[0]['sizes'][0]['url']
        except:
            continue
        # Имя и фамилия
        i = i + 1
        partner = Partner(data['id'])
        partner.set_first_name(data['first_name'])
        partner.set_last_name(data['last_name'])
        full_name = partner.first_name + " " + partner.last_name
        text = f"Анкета #{i}: {full_name}"
        #text += f"{full_name}"
        partner.set_main_photo(main_photo_url)
        VkAPI.write_msg(user, text, vk_api_with_group_token)

        # Ссылка на страницу во вконтакте
        partner.generate_profile_url()
        text = f"Профиль: {partner.profile_url}"
        VkAPI.write_msg(user, text, vk_api_with_group_token)

        # Отобразить фотографии партнёра
        show_partner_photos(partner, photos, user, vk_api_with_group_token)

        # Записываем информацию о пользователе в базу данных
        db_insert_partner(partner)

        # Записываем информацию, что этот пользователь был просмотрен
        db_insert_user_partner(user.id, data['id'])

        # Запрос на показ еще одного партнера
        VkAPI.write_msg(user, "Показать еще одного?", vk_api_with_group_token)

        while True:
            answer_of_user = VkAPI.wait_for_answer_from_user(VkLongPoll(vk_api_with_group_token))['text']
            if answer_of_user == "Да":
                break
            elif answer_of_user == "Нет":
                text = "Просмотр анкет окончен. Досвидания!"
                VkAPI.write_msg(user, text, vk_api_with_group_token)
                start_bot_execution()
                break
            else:
                text = "Не понял вашего ответа.\nПожалуйста, нажмите Да или Нет..."
                VkAPI.write_msg(user, text, vk_api_with_group_token)


# Отобразить фотографии партнёра
def show_partner_photos(partner, photos, user, vk_api_with_group_token):
    z = 0
    for photo in photos:
        if z == 3:
            break
        # Отправить фото
        attachament = partner.generate_photo_attachment_link(photo['id'])
        photo_data = {
            'user_id': user.id,
            'message': "",
            'attachment': attachament,
            'random_id': randrange(10 ** 7)
        }
        vk_api_with_group_token.method('messages.send', photo_data)
        z = z + 1


# Устанавливаем параметры, для поиска партнера
def set_search_parameters(user):
    # Пол партнера должен быть противоложным
    sex_partner = 0
    if user.sex == 1:
        sex_partner = 2
    else:
        sex_partner = 1
    # Город пользователя
    city_id = user.city_id
    # Возраст партнера
    age = int(user.age)
    age_from = age - 2
    age_to = age + 2
    request_data = {
        "sex": sex_partner,  # пол партнера для поиска
        "count": 1000,  # кол-во возвращаемых результатов
        "offset": 0,   # сдвиг
        "city": city_id,
        "status": 6,  # в активном поиске
        "age_from": age_from,  # возрат "от"
        "age_to": age_to,  # возраст "до"
        "has_photo": 1,  # у пользователя есть фотографии
        # параметры, которые должен вернуть АПИ контакта о пользователях
        "fields": {
            "first_name", "last_name", "city", "bdate",
        }
    }
    return request_data

# Выбран пункт меню "Начать поиск пары для знакомства"
def menu_start_search(user: User, vk):
    text = "Собираю информацию!"
    VkAPI.write_msg(user, text, vk)

    # Получаем информцию о пользователе и пишем в базу данных
    set_info_about_user(user, vk)
    db_insert_user(user)

    # Призыв к следующему действию
    VkAPI.write_msg(user, r"Нажмите 'Да' для продолжения.", vk)

    # Ожидаем ответ
    while True:
        answer_of_user = VkAPI.wait_for_answer_from_user(VkLongPoll(vk))['text']
        if answer_of_user == "Да":
            search_sex_partner(user, vk_api_with_group_token=vk)
            break
        elif answer_of_user == "Нет":
            text = "Если что, пиши..."
            VkAPI.write_msg(user, text, vk)
            start_bot_execution()
            break
        else:
            text = "Не понял вашего ответа.\nПожалуйста, введите ответ еще раз..."
            VkAPI.write_msg(user, text, vk)


# Заполняем в экземлпяр класса User информацию
def set_info_about_user(user: User, vk) -> dict:
    # получаем id пользователя
    VkAPI.write_msg(user, f"[+] Ваш id пользователя: {user.id}", vk)
    # получить город
    city = VkAPI.get_user_city(user, vk)
    user.set_city_title(city['title'])
    user.set_city_id(city['id'])
    VkAPI.write_msg(user, f"[+] Ваш город: {user.city_title}", vk)
    # получить пол
    sex = VkAPI.get_user_sex(user, vk)
    user.set_sex(sex)
    user_sex_text = "Женский" if user.sex == 1 else "Мужской"
    VkAPI.write_msg(user, f"[+] Ваш пол: {user_sex_text}", vk)
    # получить возраст
    age = VkAPI.get_user_age(user, vk)
    user.set_age(age)
    VkAPI.write_msg(user, f"[+] Ваш возраст: {user.age}", vk)


# Главное меню
def show_top_menu(longpoll, user, vk):
    # Показать приветственное сообщение и меню доступных действий
    text = "Добро пожаловать! \n\n"
    VkAPI.write_msg(user, text, vk)
    show_sub_menu(user, vk)
    # Анализируем ответ пользователя
    while True:
        # ждем какой пункт меню введет пользователь
        answer_of_user = VkAPI.wait_for_answer_from_user(longpoll)['text']
        # 1 => Поиск партнера для отношений
        if answer_of_user == "Да":
            menu_start_search(user, vk)
            break
        # 2 => подпрограмма, вызываемая если пользователь выбрал 2 пункт меню
        elif answer_of_user == "Нет":
            text = "Если передумаешь, пиши!"
            VkAPI.write_msg(user, text, vk)
            start_bot_execution()
            break
        # ... если введен несуществующий пункт меню
        else:
            text = "Не понял вашего ответа...\n"
            VkAPI.write_msg(user, text, vk)
            time.sleep(1)
            show_sub_menu(user, vk)


# Показать подменю
def show_sub_menu(user: User, vk):
    text = "Начать поиск анкет?"
    VkAPI.write_msg(user, text, vk)


def start_bot_execution():
    # Инициализация базы даныых
    init_database()

    # Иницииализируем vk_api
    vk = vk_api.VkApi(token=group_token)
    longpoll = VkLongPoll(vk)

    # получаем словарь с текстом пришедшим от пользователя и его user_id
    user_data = VkAPI.wait_for_answer_from_user(longpoll)
    user = User(user_data['user_id'])

    # Отобразить главное меню
    show_top_menu(longpoll, user, vk)


if __name__ == '__main__':
    print("Запуск бота:", datetime.now())
    start_bot_execution()
