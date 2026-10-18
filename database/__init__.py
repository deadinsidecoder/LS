import sqlite3
from random import choice

from .record import URLRecord
from . import queries 
from .exceptions import DBError, GenerationError, NotFoundError

from config import LENGTH, ALPHABET




DEFAULT_GENERATION_ATTEMPTS = 3


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

    def get(self, short: str, increment: bool = True) -> URLRecord | None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.INCREMENT_CLICKS if increment else queries.SELECT_BY_SHORT, (short,))
            result = cursor.fetchone()
        if result is not None:
            return URLRecord(*result)
        raise NotFoundError

    def add(self, long: str, attempts: int = DEFAULT_GENERATION_ATTEMPTS) -> URLRecord:
        if not attempts:
            raise GenerationError 
        short = "".join(choice(ALPHABET) for _ in range(LENGTH))
        cursor = self.connection.cursor()
        if (exists := cursor.execute(queries.SELECT_BY_LONG, (long,)).fetchone()) is not None:
            return URLRecord(*exists)
        try:
            with self.connection:
                result = cursor.execute(queries.INSERT, (short, long)).fetchone()
                return URLRecord(*result)
        except sqlite3.IntegrityError:
            return self.add(long, attempts - 1)
