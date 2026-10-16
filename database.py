import sqlite3
from random import choice
from dataclasses import dataclass

import queries
from config import LENGTH, ALPHABET




GENERATION_ATTEMPTS = 3


@dataclass
class URLRecord:
    id: int
    short: str
    long: str
    created_at: int
    clicks_count: int


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

    def get(self, short: str) -> URLRecord | None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.SELECT_BY_SHORT, (short,))
            result = cursor.fetchone()
        return URLRecord(*result) if result is not None else None

    def add(self, long: str) -> URLRecord:
        if (exists := self._get(long)) is not None:
            return exists
        short = self._unique_short()
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.INSERT, (short, long))
            record = cursor.fetchone()
        return URLRecord(*record)

    def _get(self, long: str) -> str | None:
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(queries.SELECT_BY_LONG, (long,))
            result = cursor.fetchone()
        return URLRecord(*result) if result is not None else None

    def _unique_short(self) -> str:
        for _ in range(GENERATION_ATTEMPTS):
            short = "".join(choice(ALPHABET) for _ in range(LENGTH))
            if self.get(short) is None:
                return short
        raise RuntimeError