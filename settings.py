import logging
import os
from pydantic import BaseSettings
from pydantic import error_wrappers

from logging_handlers import TelegramMessageHandler


DEBUG = True
BOT_TOKEN: str | None = None
ADMIN_CHAT_ID: int | None = None  # vybornyy

# load environment variables
class EnvFile(BaseSettings):
    bot_token: str
    admin_chat_id: int

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
    except Exception as error:
        logging.error(f'Invalid environment variable. {error}. ')
else:
    BOT_TOKEN = env.bot_token
    ADMIN_CHAT_ID = env.admin_chat_id

# setup logging
handlers: list[logging.Handler] = [
    logging.StreamHandler(),
]
if BOT_TOKEN is not None and ADMIN_CHAT_ID is not None:
    handlers.append(TelegramMessageHandler(BOT_TOKEN, ADMIN_CHAT_ID, logging.DEBUG))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

for handler in handlers:
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(handler)