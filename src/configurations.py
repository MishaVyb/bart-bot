import logging
from pprint import pformat
from typing import Literal

from pydantic import BaseSettings, SecretStr
from sqlalchemy.engine import URL
from telegram import __version__ as tg_version

# checking python version before starting app
try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, 'alpha', 1):
    raise RuntimeError(
        f'This example is not compatible with your current PTB version {tg_version}. To view the '
        f'{tg_version} version of this example, '
        f'visit https://docs.python-telegram-bot.org/en/v{tg_version}/examples.html'
    )


# secrets and app settings
class AppConfig(BaseSettings):
    debug: bool = True
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'DEBUG'
    sql_logs: bool = False

    bot_token: SecretStr

    botname: str = 'BartPhotosBot'
    appname: str = 'bart-bot'
    admin_id: int | None = None
    content_filepath: str = f'{appname}.content.yaml'

    db: str = 'postgresql'
    db_dialect: str = 'asyncpg'
    db_user: str
    db_password: SecretStr
    db_host: str = 'localhost'
    db_port: int = 5432
    db_name: str

    @property
    def db_url(self):
        return URL.create(
            drivername=f'{self.db}+{self.db_dialect}',
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    class Config:
        env_file = 'build.env', 'test.env', 'local.env'  # 'local.env' has the highest priority
        allow_mutation = False

    def __str__(self) -> str:
        return '\n' + pformat(self.dict())


CONFIG = AppConfig()


# logging
# TODO:

# option [1]
# logging.basicConfig(format='%(levelname)s [%(filename)s]: %(message)s', level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# # option [2]
# aa = __name__
logger = logging.getLogger(__name__)
logger.setLevel(CONFIG.log_level)

handler = logger.handlers and logger.handlers[0] or logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s [%(filename)s]: %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)
