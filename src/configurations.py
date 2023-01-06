from pydantic import BaseSettings


class Confing(BaseSettings):
    bot_token: str
    admin_chat_id: int | None
    yadisk_token: str | None
    debug: bool = True

    class Config:
        env_file = '.env'


CONFIG = Confing()
