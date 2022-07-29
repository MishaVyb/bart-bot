from pydantic import BaseSettings


class EnvFile(BaseSettings):
    bot_token: str
    admin_chat_id: int

    class Config:
        env_file = ".env"


DEBUG = True
