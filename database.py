import sqlite3
from random import choice

import queries
from config import LENGTH, ALPHABET




GENERATION_ATTEMPTS = 3


class DBManager:
    def __init__(self, path: str):
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.open()

    def open(self):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.CREATE)

    def close(self):
        self.connection.close()
        # print("closed")

    def get(self, short: str) -> str | None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.SELECT_BY_SHORT, (short,))
            result = cursor.fetchone()
        return result[0] if result is not None else None

    def add(self, long: str) -> str:
        if (exists := self._get(long)) is not None:
            return exists
        short = self._unique_short()
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.INSERT, (short, long))
        return short

    def _get(self, long: str) -> str | None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.SELECT_BY_LONG, (long,))
            result = cursor.fetchone()
        return result[0] if result is not None else None

    def _unique_short(self) -> str:
        for _ in range(GENERATION_ATTEMPTS):
            short = "".join(choice(ALPHABET) for _ in range(LENGTH))
            if self.get(short) is None:
                return short
        raise RuntimeError