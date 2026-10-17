import sqlite3
from random import choice

from .record import URLRecord
from . import queries 
from .exceptions import DBError, GenerationError, NotFoundError

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

    def get(self, short: str, increment: bool = True) -> URLRecord | None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.INCREMENT_CLICKS if increment else queries.SELECT_BY_SHORT, (short,))
            result = cursor.fetchone()
        if result is not None:
            return URLRecord(*result)
        raise NotFoundError

    def add(self, long: str) -> URLRecord:
        if (exists := self._get_by_long(long)) is not None:
            return exists
        short = self._unique_short()
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.INSERT, (short, long))
            record = cursor.fetchone()
        return URLRecord(*record)

    def _get_by_long(self, long: str) -> URLRecord | None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.SELECT_BY_LONG, (long,))
            result = cursor.fetchone()
        return URLRecord(*result) if result is not None else None

    def _get_by_short(self, short: str) -> URLRecord | None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.SELECT_BY_SHORT, (short,))
            result = cursor.fetchone()
        return URLRecord(*result) if result is not None else None

    def _unique_short(self) -> str:
        for _ in range(GENERATION_ATTEMPTS):
            short = "".join(choice(ALPHABET) for _ in range(LENGTH))
            if self._get_by_short(short) is None:
                return short
        raise GenerationError