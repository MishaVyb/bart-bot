import logging

from pydantic import BaseSettings, SecretStr
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
    bot_token: SecretStr
    yadisk_token: SecretStr

    admin_chat_id: int | None
    debug: bool = True
    appname: str = 'bart-bot'
    data_filepath: str = f'{appname}.data'
    dump_filepath: str = f'{appname}.dump.json'
    content_filepath: str = f'{appname}.content.yaml'

    admin_id: int
    admin_sharings_ids: list[int]

    class Config:
        env_file = '.env'


CONFIG = Confing()
logger.debug(f'Running application under: {CONFIG.dict()}')
