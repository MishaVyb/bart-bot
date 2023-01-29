from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import ClassVar

import pytest
from anyio import sleep
from pyrogram import Client, filters
from pyrogram.types import Message, User

from configurations import AppConfig, logger

pytest_plugins = [
    'tests.fixtures.fixture_application',
    'tests.fixtures.fixture_clients',
    'tests.fixtures.fixture_config',
    'tests.fixtures.fixture_db',
]


class TestConfig(AppConfig):
    api_id: int
    api_hash: str

    _test_phonenumbers: set[str] = set()

    @property
    def test_phonenumber(self):
        ...


@dataclass(frozen=True)
class UserIntegration:
    timeout: ClassVar = 2
    """
    Default timeout for response waiting. Seconds.
    """

    client: Client
    user: User
    target: str | int
    _messages: list[Message] = field(default_factory=list)

    def __post_init__(self):
        self.client.on_message(filters.chat(self.target))(self._handler)

    async def _handler(self, client: Client, message: Message):
        logger.info('[add message to test collection]')
        self._messages.append(message)

    @asynccontextmanager
    async def integration(self, *, timeout: int = timeout, collect: int = None):
        """
        Context manager for Telegram Bot application test integration.
        """
        self._messages.clear()

        try:
            yield self._messages
        finally:
            await sleep(timeout)
            if collect is not None:
                assert len(self._messages) == collect, 'Integration test failed. Received unexpected messages amount. '


@pytest.fixture(autouse=True)
def new_line():
    """
    Fixture simple makes new line to separate each test logging output.
    """
    print()
    yield
    print()
