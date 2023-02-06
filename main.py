import time
from datetime import datetime
from random import randrange

from api.vkontake import VkAPI
from config.settings import user_token, group_token
from database.database import db, init_database
from users.partner import Partner
from users.user import User


# Осуществляем поиск партнера, находим самые популярные фотографии и возвращаем их пользователю
def search_sex_partner(user: User, vk: VkAPI):
    # Получаем список пользователей
    request_data = set_search_parameters(user)

    # Показываем пользователю найденных половых партнеров
    text = f"Поиск закончен!\n\n Приступаю к показу анкет."
    vk.write_msg(user, text)
    time.sleep(2)

    i = 0
    for data in vk.user_search_generator(request_data):

        # Проверяем, показывали ли этого партнера его ранее
        if not db.check_is_new_partner(user.id, data['id']):
            continue
        # Получаем фотографии
        try:
            photos = vk.get_photos_of_person(data['id'])
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
        # text += f"{full_name}"
        partner.set_main_photo(main_photo_url)
        vk.write_msg(user, text)

        # Ссылка на страницу во вконтакте
        partner.generate_profile_url()
        text = f"Профиль: {partner.profile_url}"
        vk.write_msg(user, text)

        # Отобразить фотографии партнёра
        show_partner_photos(partner, photos, user, vk)

        # Записываем информацию о пользователе в базу данных
        db.insert_partner(partner)

        # Записываем информацию, что этот пользователь был просмотрен
        db.insert_user_partner(user.id, data['id'])

        # Запрос на показ еще одного партнера
        vk.write_msg(user, "Показать еще одного?")

        while True:
            answer_of_user = vk.wait_for_answer_from_user()['text']
            if answer_of_user == "Да":
                break
            elif answer_of_user == "Нет":
                text = "Просмотр анкет окончен. Досвидания!"
                vk.write_msg(user, text)
                start_bot_execution()
                return
            else:
                text = "Не понял вашего ответа.\nПожалуйста, нажмите Да или Нет..."
                vk.write_msg(user, text)


    vk.write_msg(user, "Список анкет завершен. Посмотреть заново?")
    while True:
        answer_of_user = vk.wait_for_answer_from_user()['text']
        if answer_of_user == "Да":
            db.delete_all_user_partners(user.id)
            search_sex_partner(user, vk)
            return
        elif answer_of_user == "Нет":
            text = "Просмотр анкет окончен. Досвидания!"
            vk.write_msg(user, text)
            start_bot_execution()
            return
        else:
            text = "Не понял вашего ответа.\nПожалуйста, нажмите Да или Нет..."
            vk.write_msg(user, text)


# Отобразить фотографии партнёра
def show_partner_photos(partner, photos, user, vk: VkAPI):
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
        vk.group_api.method('messages.send', photo_data)
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
        "offset": 0,  # сдвиг
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
def menu_start_search(user: User, vk: VkAPI):
    text = "Собираю информацию!"
    vk.write_msg(user, text)

    # Получаем информцию о пользователе и пишем в базу данных
    set_info_about_user(user, vk)
    db.insert_user(user)

    # Призыв к следующему действию
    vk.write_msg(user, r"Нажмите 'Да' для продолжения.")

    # Ожидаем ответ
    while True:
        answer_of_user = vk.wait_for_answer_from_user()['text']
        if answer_of_user == "Да":
            search_sex_partner(user, vk)
            break
        elif answer_of_user == "Нет":
            text = "Если что, пиши..."
            vk.write_msg(user, text)
            start_bot_execution()
            break
        else:
            text = "Не понял вашего ответа.\nПожалуйста, введите ответ еще раз..."
            vk.write_msg(user, text)


# Заполняем в экземлпяр класса User информацию
def set_info_about_user(user: User, vk: VkAPI):
    # получаем id пользователя
    vk.write_msg(user, f"[+] Ваш id пользователя: {user.id}")
    # получить город
    city = vk.get_user_city(user)
    user.set_city_title(city['title'])
    user.set_city_id(city['id'])
    vk.write_msg(user, f"[+] Ваш город: {user.city_title}")
    # получить пол
    sex = vk.get_user_sex(user)
    user.set_sex(sex)
    user_sex_text = "Женский" if user.sex == 1 else "Мужской"
    vk.write_msg(user, f"[+] Ваш пол: {user_sex_text}")
    # получить возраст
    age = vk.get_user_age(user)
    user.set_age(age)
    vk.write_msg(user, f"[+] Ваш возраст: {user.age}")


# Главное меню
def show_top_menu(user, vk: VkAPI):
    # Показать приветственное сообщение и меню доступных действий
    text = "Добро пожаловать! \n\n"
    vk.write_msg(user, text)
    show_sub_menu(user, vk)
    # Анализируем ответ пользователя
    while True:
        # ждем какой пункт меню введет пользователь
        answer_of_user = vk.wait_for_answer_from_user()['text']
        # 1 => Поиск партнера для отношений
        if answer_of_user == "Да":
            menu_start_search(user, vk)
            break
        # 2 => подпрограмма, вызываемая если пользователь выбрал 2 пункт меню
        elif answer_of_user == "Нет":
            text = "Если передумаешь, пиши!"
            vk.write_msg(user, text)
            start_bot_execution()
            break
        # ... если введен несуществующий пункт меню
        else:
            text = "Не понял вашего ответа...\n"
            vk.write_msg(user, text)
            time.sleep(1)
            show_sub_menu(user, vk)


# Показать подменю
def show_sub_menu(user: User, vk: VkAPI):
    text = "Начать поиск анкет?"
    vk.write_msg(user, text)


def start_bot_execution():
    # Инициализация базы даныых
    init_database()

    # Иницииализируем vk_api
    vk = VkAPI(user_token, group_token)

    # получаем словарь с текстом пришедшим от пользователя и его user_id
    user_data = vk.wait_for_answer_from_user()
    user = User(user_data['user_id'])

    # Отобразить главное меню
    show_top_menu(user, vk)


if __name__ == '__main__':
    print("Запуск бота:", datetime.now())
    start_bot_execution()
