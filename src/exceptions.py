class NoPhotosException(Exception):
    message = 'History has no messages. '

    def __init__(self, *args: object, message: str = message) -> None:
        super().__init__(message, *args)


class NoUserException(Exception):
    message = 'User has not started this Bot yet. '

    def __init__(self, *args: object, message: str = message) -> None:
        super().__init__(message, *args)
