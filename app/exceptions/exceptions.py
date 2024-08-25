class PermissionDenied(Exception):
    def __init__(self, message: str = "Permission denied"):
        self.message = message
        super().__init__(self.message)


class PageNotFound(Exception):
    def __init__(self, message: str = "Page not found"):
        self.message = message
        super().__init__(self.message)


class DatabaseError(Exception):
    def __init__(self, message: str = "Database error"):
        self.message = message
        super().__init__(self.message)


class BadRequestError(Exception):
    def __init__(self, message: str = "Bad request"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(Exception):
    def __init__(self, message: str = "Not found"):
        self.message = message
        super().__init__(self.message)


class InternalServerError(Exception):
    def __init__(self, message: str = "Internal server error"):
        self.message = message
        super().__init__(self.message)
