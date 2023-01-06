import logging

from pydantic import BaseSettings
from telegram import __version__ as TG_VER

# check python version before starting app
try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, 'alpha', 1):
    raise RuntimeError(
        f'This example is not compatible with your current PTB version {TG_VER}. To view the '
        f'{TG_VER} version of this example, '
        f'visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html'
    )

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logger.handlers and logger.handlers[0] or logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

# secrets
class Confing(BaseSettings):
    bot_token: str
    admin_chat_id: int | None
    yadisk_token: str | None
    debug: bool = True
    app_name = 'bart-bot'

    class Config:
        env_file = '.env'


CONFIG = Confing()
