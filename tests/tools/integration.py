import asyncio
import builtins
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

import pytest
from anyio import sleep
from pyrogram import Client, filters  # type: ignore [attr-defined]
from pyrogram.raw.functions.messages import DeleteHistory
from pyrogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from telegram import Update
from telegram.ext import Application, ApplicationHandlerStop, ContextTypes

from database.models import UserModel
from tests.conftest import TestConfig, logger


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

        self._collected_replyes: list[Message] = []
        self._collected_exceptions: list[Exception] = []
        self._collection_required_amount: int | None = None
        self._collection_max_timeout: float = config.integration_timeout_sec
        self._collection: asyncio.Event = asyncio.Event()

    def __str__(self) -> str:
        return f'<{self.target} integration ({self.credits})'

    # TODO: add backoff factor for auth fails
    @asynccontextmanager
    async def session_context(self, tag: str = ''):
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
            in_memory=(not self.config.strict_mode),
            phone_number=self.credits.phone,
            phone_code=self.config.get_confirmation_code(),
        )

        # set main *any* message handler-callback to collect received messages while acting tests:
        self.client.on_message(filters.chat(self.target))(self._collect_replyes_callback)  # type: ignore

        # set error handler-callback to store any exception received to tell pytest that integration test was failed
        #
        # NOTE
        # if native application error handler raise ApplicationHandlerStop after error handling, this error handler
        # will be omitted and 'self._collected_exceptions' list leaves empty
        # TODO transfer to app.post_init
        self.app.add_error_handler(self._collect_app_exceptions_callback)

        try:
            logger.info(f'Make authorization for {self}. ')
            # NOTE: some phonenumbers are registered already, some other not.
            # to be sure, handle sign up action by patching std input
            with self._patch_signup_inout():
                await self.client.start()

            if self.config.strict_mode:
                logger.info('Strict mode is on. Set user credentials and username. It takes a while. ')

                # update remote Telegram User properties:
                await self.client.update_profile(*self.credits.fullname)
                if self.client.me.username != self.credits.username:
                    await self.client.set_username(self.credits.username)

                await self.client.invoke(
                    DeleteHistory(peer=await self.client.resolve_peer(self.target), max_id=0, just_clear=False)
                )
                await self.client.send_message(self.config.botname, '/start')
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
    async def collect(self, *, amount: int = None, strict_mode: bool = False, exceptions: bool = True):
        """
        Context manager for Telegram Bot application test integration.

        * `amount`: how many messages is expecting to receive.
        * `strict_mode`: wait until messages received ant then sleep for `_collection_max_timeout` seconds to be sure
        there are no more messages after expected ones.
        * `exceptions`: check there are no unhandled exceptions inside app was risen.
        """
        strict_mode = strict_mode or self.config.strict_mode

        self._collection_required_amount = amount
        self._collected_replyes.clear()
        self._collected_exceptions.clear()
        self._collection.clear()

        try:
            yield self._collected_replyes
        finally:
            logger.info(f'Waiting for replyes. ({strict_mode=}, {amount=}, timeout={self._collection_max_timeout}). ')
            collection_time_start = time.time()

            if amount:
                # NOTE:
                # wait until all requested messages amount will be collected or the waiting time (timeout) will end
                # if strict_mode, then wait another `timeout` sec to be sure there are no other messages will be sent
                timout = asyncio.create_task(self._collection_max_timeout_waiting())
                await self._collection.wait()
                timout.cancel()
                if strict_mode:
                    await sleep(self._collection_max_timeout)
            else:
                await sleep(self._collection_max_timeout)

            waisted_time = time.time() - collection_time_start
            logger.info(f'Done! {len(self._collected_replyes)} replyes collected in: {waisted_time} sec. ')
            if exceptions:
                assert not self._collected_exceptions, 'Unhandled app exception received. '
            if amount:
                assert len(self._collected_replyes) == amount, 'Received unexpected messages amount. '

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
    async def user(self) -> UserModel:
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
        self._collected_exceptions.append(context.error)
        raise ApplicationHandlerStop
