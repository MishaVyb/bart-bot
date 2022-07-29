import logging
from typing import ClassVar, List

import telegram


class TelegramMessageHandler(logging.Handler):
    """Handler for logging messages by sending a telegram message."""

    data: ClassVar[List[str]] = []

    def __init__(
        self, telegram_token: str, telegram_chat_id: int, level=logging.ERROR
    ):
        """telegram_token: telegram bot token.
        telegram_chat_id: user id to which messages would be sent.
        """
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        """Logging record by sending a telegram message."""
        if record.message in self.data:
            return

        try:
            bot = telegram.Bot(self.telegram_token)
            message = self.format(record)
            bot.send_message(self.telegram_chat_id, message)
        except Exception:
            pass
        else:
            self.data.append(record.message)
