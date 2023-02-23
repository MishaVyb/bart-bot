import pytest
from telegram import User

from application.base import LayeredApplication
from configurations import AppConfig

pytestmark = pytest.mark.anyio


async def test_bot_environment(config: AppConfig, application: LayeredApplication):
    assert '/test' in application.bot.base_url

    user: User = await application.bot.get_me()
    assert user.username == config.botname
