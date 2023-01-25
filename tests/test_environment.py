from pyrogram import Client
from telegram import User

from application.base import LayeredApplication
from configurations import AppConfig


async def test_environment(vybornyy: Client, config: AppConfig, application: LayeredApplication):
    assert '/test' in application.bot.base_url

    user: User = await application.bot.get_me()
    assert user.username == config.botname
