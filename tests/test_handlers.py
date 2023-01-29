from configurations import AppConfig
from content import CONTENT
from tests.conftest import UserIntegration


async def test_start_handler(vybornyy: UserIntegration, config: AppConfig):
    async with vybornyy.integration(collect=1) as messages:
        await vybornyy.client.send_message(config.botname, '/start')

    assert messages[0].text == CONTENT.messages.start.format(username=vybornyy.user.username)
