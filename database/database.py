import psycopg2

from users.partner import Partner
from users.user import User
from config.settings import *

connection = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    dbname=database,
    port=5432
)
connection.autocommit = True


# Создаем базы данных пользователей, которые общаются с ботом
def db_create_users():
    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users(
                id serial,
                vk_id varchar(30) PRIMARY KEY,
                city_id varchar(100) NOT NULL,
                age integer NOT NULL,
                sex varchar(100) NOT NULL);"""
        )
    print("[+] Table users created")


# Добавляем пользователя
def db_insert_user(user: User):
    with connection.cursor() as cursor:
        # check user exist
        cursor.execute(
            f"""SELECT id FROM users WHERE vk_id = '{user.id}';"""
        )
        id = cursor.fetchone()
        if id:
            print(f"[-] User with vk_id={user.id} already exist")
            return
        # insert
        cursor.execute(
            f"""INSERT INTO users (vk_id, city_id, age, sex) 
            VALUES ('{user.id}', '{user.city_id}', '{user.age}', '{user.sex}');"""
        )
        print(f"[+] User with vk_id={user.id} inserted")


# Cоздаем таблицу с просмотренными партнерами
def db_create_partners():
    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS partners(
                id serial,
                vk_id varchar(30) PRIMARY KEY,
                first_name varchar(100) NOT NULL,
                last_name varchar(100) NOT NULL,
                main_photo varchar (256) NOT NULL,
                profile_url varchar(200));"""
        )
    print("[+] Table partners created")


# Добавляем просмотренного партнёра
def db_insert_partner(partner: Partner):
    with connection.cursor() as cursor:
        # check partner exist
        cursor.execute(
            f"""SELECT id FROM partners WHERE vk_id = '{partner.id}';"""
        )
        id = cursor.fetchone()
        if id:
            print(f"[-] Partner with vk_id={partner.id} already exist")
            return
        # insert
        cursor.execute(
            f"""INSERT INTO partners (vk_id, first_name, last_name, main_photo, profile_url) 
            VALUES ('{partner.id}', '{partner.first_name}', '{partner.last_name}', '{partner.main_photo}', '{partner.profile_url}');"""
        )
        print(f"[+] Partner with vk_id={partner.id} inserted")


def db_create_users_partners():
    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users_partners(
                user_vk_id varchar(30) NOT NULL REFERENCES users(vk_id),
                partner_vk_id varchar(30) NOT NULL REFERENCES partners(vk_id));"""
        )
    print("[+] Table partners created")


# Добавляем просмотренных партнеров пользователем
def db_insert_user_partner(user_vk_id, partner_vk_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""INSERT INTO users_partners (user_vk_id, partner_vk_id) 
            VALUES ('{user_vk_id}', '{partner_vk_id}');"""
        )


# Проверка, показывали ли мы партнера пользователю ранее
def db_check_is_new_partner(user_id, partner_id) -> bool:
    with connection.cursor() as cursor:
        # check partner exist
        cursor.execute(
            f"""SELECT * FROM users_partners WHERE user_vk_id = '{user_id}' AND partner_vk_id = '{partner_id}';"""
        )
        # Партнер старый
        if cursor.fetchone():
            print(f"[INFO] user with id = {partner_id} was already showed previously")
            return False
        # Партнер новый
        return True


def init_database():
    # Cоздать таблицу users
    db_create_users()
    # Создать табилцу partners
    db_create_partners()
    # Cоздать таблицу users_partners
    db_create_users_partners()


if __name__ == '__main__':
    init_database()
