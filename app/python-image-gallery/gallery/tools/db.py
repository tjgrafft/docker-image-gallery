import os
import psycopg2

class DbConnection:
    def __init__(self):
        self.connection = None

    def connect(self):
        self.connection = psycopg2.connect(
            host=os.getenv('PG_HOST'),
            dbname=os.getenv('IG_DATABASE'),
            user=os.getenv('IG_USER'),
            password=self.get_password_from_file()
        )

    def get_password_from_file(self):
        password_file = os.getenv('IG_PASSWD_FILE')
        with open(password_file, 'r') as file:
            return file.read().strip()

    def execute(self, query, args=None):
        cursor = self.connection.cursor()
        if not args:
            cursor.execute(query)
        else:
            cursor.execute(query, args)
        return cursor
