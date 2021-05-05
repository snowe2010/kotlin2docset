import sqlite3


class SQLiteConnection:
    def __init__(self, database_path: str):
        self.connection: sqlite3.Connection = sqlite3.connect(database_path)
        self.cursor: sqlite3.Cursor = self.connection.cursor()

    def drop_sqlite_search_index(self):
        try:
            print('==> Attempting to drop SQLite searchIndex table')
            self.cursor.execute("DROP TABLE searchIndex;")
        except Exception as exception:
            print(f'==> SQL index drop failed, cause: {exception}')
            pass

    def create_sqlite_search_index(self):
        try:
            print(f'==> Creating SQLite searchIndex')
            self.cursor.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
            self.cursor.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')
        except Exception as exception:
            print(f'==> SQL index creation failed, cause: {exception}')
            pass

    def insert_into_index(self, name: str, doc_type: str, path: str):
        self.cursor.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)',
                            (name, doc_type, path))

    def commit_and_close(self):
        self.connection.commit()
        self.connection.close()
