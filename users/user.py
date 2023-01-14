class User:
    def __init__(self, user_id):
        self.id = user_id
        self.city_id = ""
        self.city_title = ""
        self.age = ""
        self.sex = ""

    def set_city_id(self, value):
        self.city_id = value

    def set_age(self, value):
        self.age = value

    def set_sex(self, value):
        self.sex = value

    def set_city_title(self, value):
        self.city_title = value

    def __str__(self):
        return f"id: {self.id}, город: {self.city_id}, возраст: {self.age}"
