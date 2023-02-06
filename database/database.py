import psycopg2

from config.settings import HOST, USER, PASSWORD, DATABASE
from users.partner import Partner
from users.user import User


class Database:

    def __init__(self, host, user, password, database):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname=database,
            port=5432
        )
        self.connection.autocommit = True

    # Создаем базы данных пользователей, которые общаются с ботом
    def create_users(self, ):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS users(
                    id serial,
                    vk_id varchar(30) PRIMARY KEY
                    );"""
            )
        print("[+] Table users created")

    # Добавляем пользователя
    def insert_user(self, user: User):
        with self.connection.cursor() as cursor:
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
                f"""INSERT INTO users (vk_id) 
                VALUES ('{user.id}');"""
            )
            print(f"[+] User with vk_id={user.id} inserted")

    # Cоздаем таблицу с просмотренными партнерами
    def create_partners(self, ):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS partners(
                    id serial,
                    vk_id varchar(30) PRIMARY KEY);
                    """
            )
        print("[+] Table partners created")

    # Добавляем просмотренного партнёра
    def insert_partner(self, partner: Partner):
        with self.connection.cursor() as cursor:
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
                f"""INSERT INTO partners (vk_id) 
                VALUES ('{partner.id}');"""
            )
            print(f"[+] Partner with vk_id={partner.id} inserted")

    def create_users_partners(self, ):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS users_partners(
                    user_vk_id varchar(30) NOT NULL REFERENCES users(vk_id),
                    partner_vk_id varchar(30) NOT NULL REFERENCES partners(vk_id));"""
            )
        print("[+] Table partners created")

    # Добавляем просмотренных партнеров пользователем
    def insert_user_partner(self, user_vk_id, partner_vk_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""INSERT INTO users_partners (user_vk_id, partner_vk_id) 
                VALUES ('{user_vk_id}', '{partner_vk_id}');"""
            )
            print(f"[+] User with vk_id={user_vk_id} and partner with vk_id={partner_vk_id} inserted")

    def delete_all_user_partners(self, user_vk_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""DELETE FROM users_partners WHERE user_vk_id = '{user_vk_id}';"""
            )

    # Проверка, показывали ли мы партнера пользователю ранее
    def check_is_new_partner(self, user_id, partner_id) -> bool:
        with self.connection.cursor() as cursor:
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


db = Database(
    user=USER,
    password=PASSWORD,
    host=HOST,
    database=DATABASE
)


def init_database():
    # Cоздать таблицу users
    db.create_users()
    # Создать табилцу partners
    db.create_partners()
    # Cоздать таблицу users_partners
    db.create_users_partners()


if __name__ == '__main__':
    init_database()
