import sqlite3
from dataclasses import dataclass




@dataclass
class LinkModel:
    id: int
    short: str
    long: str
    created_at: int
    clicks_count: int

    @classmethod
    def row_factory(cls, cursor: sqlite3.Cursor, row: tuple) -> LinkModel:
        return cls(**{column: value for (column, *_), value in zip(cursor.description, row)})


def connect(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = LinkModel.row_factory
    with connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short TEXT NOT NULL UNIQUE,
            long TEXT NOT NULL,
            created_at INTEGER NOT NULL DEFAULT (unixepoch()),
            clicks_count INTEGER NOT NULL DEFAULT 0
        )""")
    return connection


def add(connection: sqlite3.Connection, short: str, long: str) -> LinkModel:
    with connection:
        result = connection.execute(
            "INSERT INTO links (short, long) VALUES (?, ?) ON CONFLICT(short) DO NOTHING RETURNING *",
            (short, long)    
        ).fetchone()
    return result


def click(connection: sqlite3.Connection, short: str) -> None | LinkModel:
    with connection:
        result = connection.execute(
            "UPDATE links SET clicks_count = clicks_count + 1 WHERE short = ? RETURNING *",
            (short,)
        ).fetchone()
    return result


def fetch(connection: sqlite3.Connection, short: str | None = None) -> list[LinkModel]:
    return connection.execute(
        "SELECT * FROM links" if short is None else "SELECT * FROM links WHERE short = ?",
        (() if short is None else (short,))
    ).fetchall()




if __name__ == "__main__":
    connection = connect(":memory:")

    add(connection, "1", "first")
    add(connection, "2", "second")
    add(connection, "3", "third")

    assert add(connection, "1", "fourth") is None
    assert click(connection, "4") is None
    assert click(connection, "2").long == "second"
    assert click(connection, "2").clicks_count == 2