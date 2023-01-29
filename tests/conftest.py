import asyncio
import builtins
import random
import string
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

import pytest
from anyio import sleep
from pyrogram import Client, filters
from pyrogram.errors.exceptions import bad_request_400
from pyrogram.types import Message, User
from sqlalchemy.orm import Session

from configurations import AppConfig, logger
from database import crud
from database.models import UserModel

pytest_plugins = [
    'tests.fixtures.fixture_application',
    'tests.fixtures.fixture_clients',
    'tests.fixtures.fixture_config',
    'tests.fixtures.fixture_db',
]


@pytest.fixture(scope="session")
def event_loop():
    # by default pytest-asyncio define 'event_loop' as function scoped fixture
    # but we need it with session scope
    return asyncio.get_event_loop()


class TestConfig(AppConfig):
    api_id: int
    api_hash: str

    username_postfix_len: int = 4
    integration_timeout_sec: float = 2.0

    _phonenumbers: set[str] = {'9996612048'}
    _dc_number: int = 1

    def get_phonenumber(self):
        return self._phonenumbers.pop()  # FIXME

    def get_confirmation_code(self):
        return str(self._dc_number) * 5

    def get_username(cls, tag: str):
        postfix = ''.join(random.choice(string.ascii_lowercase) for _ in range(cls.username_postfix_len))
        return tag + postfix


class ClientIntegration:
    @dataclass(frozen=True)
    class Credentials:
        phone: str
        username: str
        first_name: str
        last_name: str

        @property
        def fullname(self):
            return self.first_name, self.last_name

    def __init__(self, config: TestConfig, db_session: Session | None = None) -> None:
        self.db_session = db_session
        self.config = config
        self.target = config.botname
        self.timeout = config.integration_timeout_sec

        self._messages: list[Message] = []

    # TODO: add backoff factor for auth fails
    @asynccontextmanager
    async def context(self, tag: str = ''):
        self.tag = tag
        self.credits = ClientIntegration.Credentials(
            phone=self.config.get_phonenumber(),
            username=self.config.get_username(self.tag),
            first_name=f'{self.tag}-first-name',
            last_name=f'{self.tag}-last-name',
        )

        self.client = Client(
            f'{self.tag}-test-client',
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            test_mode=True,
            in_memory=True,
            phone_number=self.credits.phone,
            phone_code=self.config.get_confirmation_code(),
        )

        # set main messages interceptor to collect received messages while acting tests:
        self.client.on_message(filters.chat(self.target))(self._handler)  # type: ignore

        logger.info(f'Authorize {self}. ')
        try:
            # NOTE: some phonenumbers are registered already, some other not.
            # to be sure, handle sign up action by patching std input
            with self._patch_signup_inout():
                await self.client.start()

            # update local User properties (it has been initialized at client.start() call above)
            self.tg_user.first_name, self.tg_user.last_name = self.credits.fullname
            self.tg_user.username = self.credits.username

            # update remote User properties
            try:
                await self.client.set_username(self.credits.username)
            except bad_request_400.UsernameNotModified as e:
                logger.warning(e)
            await self.client.update_profile(*self.credits.fullname)

            # TODO stop chat with target bot and /start it again
            # TODO kill all other potential account sessions for current phonenumber
            # TODO set 2 factor auth (that potentials other account sessions won't use it while testing)

            yield self
        finally:
            try:
                await self.client.set_username(None)
                await self.client.stop()
            except ConnectionError as e:
                logger.warning(f'Stopping cliend fails. Detail: {e}')

    @asynccontextmanager
    async def collect(self, *, amount: int = None, timeout: float = None):
        """
        Context manager for Telegram Bot application test integration.
        """
        self._messages.clear()

        try:
            yield self._messages
        finally:
            await sleep(timeout or self.timeout)  # FIXME stupid sleep statement, handle coroutine waitings
            if amount is not None:
                assert len(self._messages) == amount, 'Integration test failed. Received unexpected messages amount. '

    @contextmanager
    def _patch_signup_inout(self):
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(builtins, 'input', self._mock_input_callback)
            monkeypatch.setattr(builtins, 'print', self._mock_print_callback)
            yield

    def _mock_input_callback(self, prompt: str = ''):
        if 'Enter first name: ' == prompt:
            reply = self.credits.first_name
            logger.debug(f'[mock input] {prompt} {reply}')
            return reply

        if 'Enter last name (empty to skip): ' == prompt:
            reply = self.credits.last_name
            logger.debug(f'[mock input] {prompt} {reply}')
            return reply

        raise ValueError(prompt)

    def _mock_print_callback(self, *args, **kwargs):
        logger.debug(f'[mock output] {args} {kwargs}')

    @property
    def tg_user(self) -> User:
        if not self.client.me:
            raise ValueError

        return self.client.me

    @property
    def db_user(self) -> UserModel:
        return crud.get_or_create(self.db_session, UserModel, dict(id=self.tg_user.id), echo=True)

    async def _handler(self, client: Client, message: Message):
        logger.info('[add message to test collection]')
        self._messages.append(message)


@pytest.fixture(autouse=True, scope='function')
def aaa_new_line_function():
    """
    Fixture simple makes new line to separate each test logging output.
    """
    print()
    logger.debug('[start test function scope]')
    yield
    logger.debug('[end test function scope]')
    print()


@pytest.fixture(autouse=True, scope='session')
def aaa_new_line_session():
    """
    Fixture simple makes new line to separate each test logging output.
    """
    print()
    logger.debug('[start test session scope]')
    yield
    logger.debug('[end test session scope]')
    print()
