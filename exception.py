class CustomBaseException(Exception):
    def __init__(
        self,
        message="An error occurred.",
    ):
        super().__init__(message)
        self.message = message
