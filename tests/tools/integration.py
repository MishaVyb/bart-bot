import asyncio
import builtins
import re
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from random import randint
from typing import ClassVar

import pytest
from anyio import sleep
from pyrogram import Client, filters  # type: ignore [attr-defined]
from pyrogram.raw.functions.messages import DeleteHistory  # type: ignore [attr-defined]
from pyrogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from telegram import Update
from telegram.ext import Application, ApplicationHandlerStop, ContextTypes

from database.models import UserModel
from tests.conftest import TestConfig, logger
from utils import randstr


@dataclass(frozen=True)
class ClientCredentials:
    phone: str
    username: str
    first_name: str
    last_name: str
    bio: str = ''

    _allocated_phonenumbers: ClassVar[set[str]] = set()
    """Set of numbers already in use."""
    _DC: ClassVar[int] = 1
    """Telegram Test DC number [1, 3]"""

    @property
    def profile(self):
        return self.first_name, self.last_name, self.bio

    @classmethod
    def from_tag(cls, tag: str = '', phone: str | None = None):
        phone = phone or cls._generate_phonenumber()
        if phone in cls._allocated_phonenumbers:
            raise ValueError(phone)
        cls._allocated_phonenumbers.add(phone)

        return cls(
            phone=phone,
            username=tag + randstr(4),
            first_name=f'{tag}-first-name',
            last_name=f'{tag}-last-name',
            bio=f'{tag}-bio',
        )

    def get_confirmation_code(self):
        """
        Extract `DC` number from phone and repeat in 5 times. Docs: https://core.telegram.org/api/auth#test-accounts
        """
        match = re.match(r'99966(?P<DC>[0-3]{1})(?P<rand_part>[0-9]{4})', self.phone)
        assert match
        return match.group('DC') * 5

    @classmethod
    def _generate_phonenumber(cls):
        number = '99966' + str(cls._DC) + str(randint(1000, 9999))
        if number in cls._allocated_phonenumbers:
            raise cls._generate_phonenumber()  # another try
        return number


class ClientIntegration:
    """
    Helper class with essential tools for Telegram Bot application test integration.

    ### Base Usage.

    >>> controller = ClientIntegration(...)
    >>> with controller.session_context() as controller:                        # open test session scope
    ...     ...
    ...     with controller.collect(amount=2) as replyes:                       # open test case
    ...         cotroller.client.send_message('<bot_name>', 'Hellow, Bot!')
    ...
    ...     assert replyes[0].text == 'Hellow, Human!'                          # make assertion
    ...     assert replyes[1].text == 'Or you are not a human?..'

    """

    def __init__(self, app: Application, config: TestConfig, db_session: AsyncSession | None = None) -> None:
        self.app = app
        self.db_session = db_session
        self.config = config
        self.target = config.botname
        """Target Bot name. """

        self._collected_replyes: list[Message] = []
        self._collected_exception: Exception | None = None
        self._collection_required_amount: int | None = None
        self._collection_max_timeout: float = config.integration_timeout_sec
        self._collection: asyncio.Event = asyncio.Event()

    def __str__(self) -> str:
        return f'<{self.target} integration ({self.credits})'

    # TODO: add backoff factor for auth fails
    @asynccontextmanager
    async def session_context(self, tag: str = ''):
        """
        Provide context for test session scope. Start `pyrogram.client` and listenings for all messages from Bot.
        """
        self.tag = tag
        self.credits = ClientCredentials.from_tag(tag, self.config.get_phonenumber())
        self.client = Client(
            f'{self.tag}-test-client',
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            test_mode=True,
            in_memory=(not self.config.strict_mode),
            phone_number=self.credits.phone,
            phone_code=self.credits.get_confirmation_code(),
        )

        # set main *any* message handler-callback to collect received messages while acting tests:
        self.client.on_message(filters.chat(self.target))(self._collect_replyes_callback)  # type: ignore

        # set error handler-callback to store any exception received to tell pytest that integration test was failed
        #
        # NOTE
        # if native application error handler raise ApplicationHandlerStop after error handling, this error handler
        # will be omitted and 'self._collected_exceptions' list leaves empty
        # TODO transfer to app.post_init
        self.app.add_error_handler(self._collect_app_exceptions_callback)  # type: ignore

        try:
            logger.info(f'Make authorization for {self}. ')
            # NOTE: some phonenumbers are registered already, some other not.
            # to be sure, handle sign up action by patching std input
            with self._patch_signup_inout():
                await self.client.start()

            if self.config.strict_mode:
                logger.info('Strict mode is on. Set user credentials and username. It takes a while. ')

                # update remote Telegram User properties:
                await self.client.update_profile(*self.credits.profile)
                if self.client.me.username != self.credits.username:
                    await self.client.set_username(self.credits.username)

                await self.client.invoke(
                    DeleteHistory(peer=await self.client.resolve_peer(self.target), max_id=0, just_clear=False)
                )
                # await self.client.send_message(self.config.botname, '/start') # UNUSED
                # TODO kill all other potential account sessions for current phonenumber
                # TODO set 2 factor auth (that potentials other account sessions won't use it while testing)

            yield self
        finally:
            try:
                if self.config.strict_mode:
                    await self.client.set_username(None)

                await self.client.stop()
            except ConnectionError as e:
                logger.warning(f'Stopping client fails: {e}')

    @asynccontextmanager
    async def collect(self, *, amount: int = None, strict_mode: bool = False, rises: bool = True):
        """
        Provide context for single test case. Collecting all messages from Bot and make basic assertions.

        * `amount`: how many messages is expected to receive.
        * `strict_mode`: wait until messages received and then sleep for `_collection_max_timeout` seconds to be sure
        there are no more messages after expected ones.
        * `rises`: check there are no unhandled exception inside app was risen.
        """
        strict_mode = strict_mode or self.config.strict_mode
        self._collection_required_amount = amount
        self._collection.clear()
        self._collected_replyes.clear()
        self._collected_exception = None

        try:
            yield self._collected_replyes
        finally:
            logger.info(f'Waiting for replyes. ({strict_mode=}, {amount=}, timeout={self._collection_max_timeout}). ')
            collection_time_start = time.time()

            # NOTE. At exiting from this generator we wait until:
            # - all requested messages amount will be collected
            # - or some unhandled app exception occurs
            # - or the waiting time (timeout) will end.
            timout = asyncio.create_task(self._collection_max_timeout_waiting())
            await self._collection.wait()
            timout.cancel()

            if strict_mode:  # to be sure there are no other (extra) messages
                await sleep(self._collection_max_timeout)

            waisted_time = time.time() - collection_time_start
            logger.info(f'Done! {len(self._collected_replyes)} replyes collected in: {round(waisted_time, 3)} sec. ')

            # Test assertions:
            if self._collected_exception:
                logger.error(f'Unhandled app exception received: {self._collected_exception}. ')
                if rises:
                    raise self._collected_exception
            if amount:
                assert len(self._collected_replyes) == amount, 'Received unexpected messages amount. '

    @contextmanager
    def _patch_signup_inout(self):
        def mock_input_callback(self, prompt: str = ''):
            if 'Enter first name: ' == prompt:
                reply = self.credits.first_name
                logger.debug(f'[mock input] {prompt} {reply}')
                return reply
            if 'Enter last name (empty to skip): ' == prompt:
                reply = self.credits.last_name
                logger.debug(f'[mock input] {prompt} {reply}')
                return reply

            logger.warning(f'[invalid prompt] {prompt}')
            return ''

        def mock_print_callback(self, *args, **kwargs):
            logger.debug(f'[mock output] {args} {kwargs}')

        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(builtins, 'input', mock_input_callback)
            monkeypatch.setattr(builtins, 'print', mock_print_callback)
            yield

    @property
    async def user(self) -> UserModel:
        """
        Shortcut for accessing user from database. `Session` should be provided before.
        """
        if not self.db_session:
            raise RuntimeError(f'None {AsyncSession}. Assignee it to {self.db_session=} before. ')

        tg_user = await self.client.get_me() if self.config.strict_mode else self.client.me
        assert tg_user

        user_query = (
            select(UserModel)
            .filter(UserModel.id == tg_user.id)
            .options(
                selectinload(UserModel.history),
                selectinload(UserModel.storage),
            )
        )
        db_user = (await self.db_session.execute(user_query)).scalar_one()
        db_user.tg = tg_user
        return db_user

    async def _collection_max_timeout_waiting(self):
        await sleep(self._collection_max_timeout)
        self._collection.set()

    async def _collect_replyes_callback(self, client: Client, message: Message):
        self._collected_replyes.append(message)
        logger.info(f'Add message to test collection: {len(self._collected_replyes)}. ')

        if len(self._collected_replyes) == self._collection_required_amount:
            self._collection.set()

    async def _collect_app_exceptions_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self._collected_exception:
            logger.error(context.error)
            return

        self._collected_exception = context.error
        self._collection.set()
        raise ApplicationHandlerStop  # UNUSED
