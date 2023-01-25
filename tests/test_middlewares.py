from contextlib import asynccontextmanager

from anyio import sleep
from conftest import logger
from pyrogram import Client, filters
from pyrogram.types import Message

from configurations import CONFIG, AppConfig
from content import CONTENT


# TODO
# move to vybornyy Clint method (Custom Client class)
#
@asynccontextmanager
async def integration(client: Client, *, timeout: int = 2, collect: int | None = None, config: AppConfig = CONFIG):
    """
    Context manager for Telegram Bot application test integration.
    """
    messages: list[Message] = []

    @client.on_message(filters.chat(config.botname))  # type: ignore
    async def handler(client: Client, message: Message):
        logger.info('[message add to test collection]')
        messages.append(message)

    try:
        yield messages
    finally:
        await sleep(timeout)
        if collect is not None:
            assert len(messages) == collect, 'Integration test failed. Received unexpected messages amount. '


async def test_start_handler(vybornyy: Client, config: AppConfig):
    async with integration(vybornyy, collect=1) as messages:
        await vybornyy.send_message(config.botname, '/start')

    assert messages[0].text == CONTENT.messages.start.format(username='???')
