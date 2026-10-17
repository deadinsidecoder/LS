class DBError(Exception):
    pass


class GenerationError(DBError):
    pass


class NotFoundError(DBError):
    pass