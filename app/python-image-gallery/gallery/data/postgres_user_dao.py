from ..tools.db import DbConnection
from .user import User
from .user_dao import UserDAO

db = DbConnection()

class PostgresUserDAO(UserDAO):
    def __init__(self):
        pass

    def get_users(self):
        result = []
        cursor = db.execute("select username,password,full_name from users")
        for t in cursor.fetchall():
            result.append(User(t[0], t[1], t[2]))
        return result
    
    def delete_user(self, username):
        db.execute("delete from users where username=%s", (username,))
        return     

    def get_user_by_username(self, username):
        cursor = db.execute("select username,password,full_name from users where username=%s", (username,))
        row = cursor.fetchone()
        if row is None:
            return None
        else:
            return User(row[0], row[1], row[2])

    def insert_user(self, username, password, full_name):
        db.execute("INSERT INTO users (username, password, full_name) VALUES (%s, %s, %s)", (username, password, full_name))
        db.connection.commit()

    def update_user(self, username, new_password, new_fullname):
        db.execute("UPDATE users SET password = %s, full_name = %s WHERE username = %s", (new_password, new_fullname, username))
        db.connection.commit()

    def get_owner_by_filename(self, filename):
        cursor = db.execute("SELECT owner FROM images WHERE filename = %s", (filename,))
        row = cursor.fetchone()
        return row[0] if row else None

    def delete_image(self, filename):
        db.execute("DELETE FROM images WHERE filename = %s", (filename,))
        db.connection.commit()

        