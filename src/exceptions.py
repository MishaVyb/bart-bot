class NoPhotosException(BaseException):
    message = 'History has no messages. '

    def __init__(self, *args: object, message: str = message) -> None:
        super().__init__(message, *args)
