import logging
from typing import Literal

from pydantic import BaseSettings, SecretStr
from telegram import __version__ as TG_VER

# checking python version before starting app
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

# secrets and app settings
class Confing(BaseSettings):
    debug: bool = True
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'DEBUG'
    sql_logs: bool = True

    bot_token: SecretStr
    yadisk_token: SecretStr

    admin_chat_id: int | None
    appname: str = 'bart-bot'
    remote_filepath: str = f'{appname}.data'
    dump_filepath: str = f'{appname}.dump.json'
    content_filepath: str = f'{appname}.content.yaml'

    admin_id: int
    admin_sharings_ids: list[int]

    db: str = 'postgresql'
    db_dialect: str = 'asyncpg'
    db_user: str
    db_password: SecretStr
    db_host: str = 'localhost'
    db_port: int = 5432
    db_name: str = 'bartbot'

    def db_uri(self, db: str = None, dialect: str = None, host: str = None, port: int = None, name: str = None):
        db = db or self.db
        dialect = dialect or self.db_dialect
        user = self.db_user
        password = self.db_password.get_secret_value()
        host = host or self.db_host
        port = port or self.db_port
        name = name or self.db_name
        return f'{db}+{dialect}://{user}:{password}@{host}:{port}/{name}'

    class Config:
        env_file = '.env'
        allow_mutation = False


CONFIG = Confing()

# logging
#
# TODO: add PTB logs...
logger = logging.getLogger(__name__)
logger.setLevel(CONFIG.log_level)

handler = logger.handlers and logger.handlers[0] or logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

logger.debug(f'Running application under: {CONFIG.dict()}')
