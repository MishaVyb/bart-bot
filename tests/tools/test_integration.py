import pytest
from telegram.ext import Application, CommandHandler

from configurations import AppConfig
from tests.tools.integration import ClientIntegration

pytestmark = pytest.mark.anyio


async def test_integration_exceptions_collector(
    application: Application, vybornyy: ClientIntegration, config: AppConfig
):
    """
    Arrange:
    - add broken handler to application handlers

    Test case:
    - send command to invoke that handler
    - expecting an error will be risen
    """

    application.add_handler(CommandHandler('error', lambda u, c: 1 / 0), group=-1)  # -1 for highest priority

    vybornyy._collection_max_timeout = 10.0
    with pytest.raises(ZeroDivisionError):
        async with vybornyy.collect():
            await vybornyy.client.send_message(config.botname, '/error')

    # check no exception in right handler:
    await vybornyy.client.send_message(config.botname, '/start')
