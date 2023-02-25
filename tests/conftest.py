import builtins
import logging
import random
import string
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

import pytest
from anyio import sleep
from pyrogram import Client, filters
from pyrogram.errors.exceptions import bad_request_400
from pyrogram.types import Message, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from telegram.ext import Application

from application.context import CustomContext
from configurations import AppConfig
from database.models import UserModel

logger = logging.getLogger(__name__)
logger.setLevel('WARNING')

pytest_plugins = [
    'tests.fixtures.fixture_application',
    'tests.fixtures.fixture_clients',
    'tests.fixtures.fixture_config',
    'tests.fixtures.fixture_db',
    'tests.fixtures.fixture_images',
]


# UNUSED
# @pytest.fixture(scope="session")
# def event_loop():
#     # by default pytest-asyncio define 'event_loop' as function scoped fixture
#     # but we need it with session scope
#     return asyncio.get_event_loop()


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


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

    def __init__(self, app: Application, config: TestConfig, db_session: AsyncSession | None = None) -> None:
        self.app = app
        self.db_session = db_session
        self.config = config
        self.target = config.botname  # TODO: create telegram bot from @BotFather dynamically
        self.timeout = config.integration_timeout_sec

        self._collected_replyes: list[Message] = []
        self._collected_exceptions: list[Exception] = []

    def __str__(self) -> str:
        return f'<{self.target} integration ({self.credits})'

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

        # set main *any* message handler-callback to collect received messages while acting tests:
        self.client.on_message(filters.chat(self.target))(self._client_message_registry)  # type: ignore

        # set error handler-callback to store any exception received to tell paytest that integration test was failed
        #
        # NOTE
        # if native application error handler rise ApplicationHandlerStop after error handling, this error handler
        # will be omitted and 'self._collected_exceptions' list leaves empty
        self.app.add_error_handler(self._app_exception_registry)

        logger.info(f'Make authorization for {self}. ')
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
                logger.debug(e)
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
                logger.warning(f'Stopping client fails: {e}')

    @asynccontextmanager
    async def collect(self, *, amount: int = None, timeout: float = None, strict: bool = True):
        """
        Context manager for Telegram Bot application test integration.
        """
        timeout = timeout if timeout is not None else self.timeout
        self._collected_replyes.clear()
        self._collected_exceptions.clear()

        try:
            yield self._collected_replyes
        finally:
            logger.info(f'Waiting for replyes ({timeout} sec). ' if timeout else 'No waiting for reply. ')
            await sleep(timeout)  # FIXME stupid sleep statement, handle coroutine waitings

            if strict:
                assert not self._collected_exceptions, 'Integration test failed. Unhandled app exception received. '
            if amount is not None:
                assert (
                    len(self._collected_replyes) == amount
                ), 'Integration test failed. Received unexpected messages amount. '

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
            raise ValueError(f'None {User}. Call for {self.context} before. ')

        return self.client.me

    @property
    async def db_user(self) -> UserModel:
        if not self.db_session:
            raise RuntimeError(f'None {AsyncSession}. Assignee it to {self.db_session=} before. ')

        user_query = (
            select(UserModel)
            .filter(UserModel.id == self.tg_user.id)
            .options(selectinload(UserModel.history))  # fmt: off
        )
        return (await self.db_session.execute(user_query)).scalar_one()

    async def _client_message_registry(self, client: Client, message: Message):
        logger.info('[add message to test collection]')
        self._collected_replyes.append(message)

    async def _app_exception_registry(self, update: object, context: CustomContext):
        self._collected_exceptions.append(context.error)


# FIXME make those fixture to be called before any other
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
