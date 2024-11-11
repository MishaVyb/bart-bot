import logging
from datetime import timezone
from pathlib import Path
from pprint import pformat
from typing import Literal

from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseSettings, DirectoryPath, FilePath, SecretStr
from sqlalchemy.engine import URL


class AppConfig(BaseSettings):
    app_title: str = ''
    debug: bool = True
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'DEBUG'
    sql_logs: bool = False

    bot_token: SecretStr
    botname: str = 'BartPhotosBot'
    admin_id: int | None = None

    base_dir: DirectoryPath = Path().resolve(__file__)
    content_filepath: FilePath = base_dir / f'bart-bot.content.yaml'
    dump_filepath: FilePath | None

    send_feed_me_chat_ids: list[int] = []
    send_feed_me_message_crons: list[CronTrigger] = [
        CronTrigger(
            hour=4,
            minute=0,
            timezone=timezone.utc,
        ),
        CronTrigger(
            hour=9,
            minute=0,
            timezone=timezone.utc,
        ),
        CronTrigger(
            hour=16,
            minute=0,
            timezone=timezone.utc,
        ),
        # VBRN for local testing:
        # CronTrigger(
        #     hour=datetime.now(timezone.utc).hour,
        #     minute=(datetime.now(timezone.utc) + timedelta(minutes=1)).minute,
        #     timezone=timezone.utc,
        # ),
    ]

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

# Logging.
logger = logging.getLogger(__name__)
logger.setLevel(CONFIG.log_level)

handler = logger.handlers and logger.handlers[0] or logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s [%(name)s] %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

logging.getLogger('apscheduler').setLevel(logging.DEBUG)
logging.getLogger('apscheduler').addHandler(handler)
