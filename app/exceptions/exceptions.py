class PermissionDenied(Exception):
    def __init__(self, message: str = "Permission denied"):
        self.message = message
        super().__init__(self.message)


class PageNotFound(Exception):
    def __init__(self, message: str = "Page not found"):
        self.message = message
        super().__init__(self.message)
