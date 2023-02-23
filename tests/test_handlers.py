import pytest
from configurations import AppConfig
from content import CONTENT
from tests.conftest import ClientIntegration

pytestmark = pytest.mark.anyio


async def test_start_handler(vybornyy: ClientIntegration, config: AppConfig):
    async with vybornyy.collect(amount=1) as replyes:
        await vybornyy.client.send_message(config.botname, '/start')

    assert replyes[0].text == CONTENT.messages.start.format(username=vybornyy.tg_user.username)
