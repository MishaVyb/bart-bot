import logging
import os
from pydantic import BaseSettings
from pydantic import error_wrappers

from logging_handlers import TelegramMessageHandler




DEBUG = False
BOT_TOKEN: str | None = None        # BartPhotosBot token
ADMIN_CHAT_ID: int | None = None    # vybornyy
YADISK_TOKEN: str | None = None     # vybornyy yandex disk token



# ------------- load environment variables -------------
class EnvFile(BaseSettings):
    bot_token: str
    admin_chat_id: int
    yadisk_token: str

    class Config:
        env_file = ".env"

try:
    env = EnvFile()
except error_wrappers.ValidationError as error:
    logging.warning(
        f'Invalid env file. {error}. Getting variables from os environment.'
    )
    try:
        BOT_TOKEN = str(os.getenv('BOT_TOKEN'))
        ADMIN_CHAT_ID = int(str(os.getenv('ADMIN_CHAT_ID')))
        YADISK_TOKEN = str(os.getenv('YADISK_TOKEN'))
    except Exception as error:
        logging.error(f'Invalid environment variable. {error}. ')
else:
    BOT_TOKEN = env.bot_token
    ADMIN_CHAT_ID = env.admin_chat_id
    YADISK_TOKEN = env.yadisk_token



# ---------- setup logging -------------
handlers: list[logging.Handler] = [
    logging.StreamHandler(),
]
if BOT_TOKEN is not None and ADMIN_CHAT_ID is not None:
    handlers.append(TelegramMessageHandler(BOT_TOKEN, ADMIN_CHAT_ID, logging.ERROR))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

for handler in handlers:
    handler.setFormatter(
        # logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.Formatter(
            '%(filename)s: '
            '%(levelname)s: '
            '%(funcName)s(): '
            '%(lineno)d:\t'
            '%(message)s'
        )
    )
    logger.addHandler(handler)
