class ProjectNotFoundError(Exception):
    def __init__(self, message="Project not found"):
        self.message = message
        super().__init__(self.message)


class DatabaseError(Exception):
    def __init__(self, message="An error occurred while accessing the database"):
        self.message = message
        super().__init__(self.message)


class NotAuthorizedError(Exception):
    def __init__(self, message="Not authorized to perform this action"):
        self.message = message
        super().__init__(self.message)
