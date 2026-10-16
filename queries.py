CREATE = """CREATE TABLE IF NOT EXISTS urls (
    short TEXT UNIQUE,
    long TEXT UNIQUE
)"""

SELECT_BY_SHORT = "SELECT long FROM urls WHERE short = ?"

SELECT_BY_LONG = "SELECT short FROM urls WHERE long = ?"

INSERT = "INSERT INTO urls (short, long) VALUES (?, ?)"