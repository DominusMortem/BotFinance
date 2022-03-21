import sqlite3


class Database:

    def __init__(self):
        self.db = sqlite3.connect("finance.db", check_same_thread=False)
        self.cursor = self.db.cursor()
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS category(
           cat_id INT PRIMARY KEY,
           cat_name TEXT,
           user_id TEXT);
        """
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS product(
           prod_id INT PRIMARY KEY,
           prod_name TEXT,
           cat_id TEXT,
           price TEXT,
           prod_count TEXT,
           date TEXT,
           user_id TEXT);
        """
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS cash(
           cash_id INT PRIMARY KEY,
           balance TEXT,
           date TEXT,
           desc TEXT,
           user_id TEXT);
        """
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS bank(
           bank_id INT PRIMARY KEY,
           balance TEXT,
           date TEXT,
           user_id TEXT);
        """
        )
        self.db.commit()

    def query(self, ql):
        self.cursor.execute(ql)
        answer = self.cursor.fetchall()
        if answer:
            return answer
        else:
            return

    def create(self, ql, arg):
        self.cursor.execute(ql, arg)
        self.db.commit()

    def __del__(self):
        self.db.close()
