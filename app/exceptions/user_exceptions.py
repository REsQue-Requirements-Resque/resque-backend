class DuplicateEmailError(Exception):
    def __init__(self, message="Email already exists"):
        self.message = message
        super().__init__(self.message)


class DatabaseError(Exception):
    def __init__(self, message="An error occurred while accessing the database"):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsError(Exception):
    pass


class TooManyAttemptsError(Exception):
    pass
