"""
Module to describe application's middleware as context manager wrappers. Example:

@asynccontextmanager
async def session_context(update: Update, context: CustomContext):
    <setup>
    try:
        <add some attrubutes to context>
        yield
    finally:
        <cleanup>

NOTE:
Only `yield None` is allowed, because:
* `@asynccontextmanager` -> return help-object with `AsyncContextDecorator` in bases
* We use its `__call__` to wrap our handler defined middleware.
* But __call__ do noghing with yielded value and we cannot use it anyhow.
* So there is the reason to pass any values directly to update context
"""

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session
from telegram import Update

from application.context import CustomContext
from configurations import CONFIG, logger
from database import crud
from database.models import UserModel


@asynccontextmanager
async def session_context():
    # ??? define engine in scope for every update or globally for all app only once in beginnings
    #
    logger.debug('session context in')

    engine = create_async_engine(CONFIG.db_uri(), echo=CONFIG.sql_logs)
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
    await engine.dispose()

    logger.debug('session context out')


@asynccontextmanager
async def session_middleware(update: Update, context: CustomContext):
    logger.debug('session middleware in')
    async with session_context() as session:
        setattr(context, 'session', session)
        yield
        try:
            delattr(context, 'session')
        except Exception:
            logger.error(f'Delleting session attr failed. ')  # FIXME

    logger.debug('session middleware out')


@asynccontextmanager
async def user_middleware(update: Update, context: CustomContext):
    # ???
    # why sync (not async) here
    def _sync(session: Session):
        user = crud.get_or_create(session, UserModel, dict(id=update.effective_user.id), echo=True)  # type: ignore
        ...
        #
        # TODO: merge user from DB with user from API

    await context.session.run_sync(_sync)
    yield
    #
    # TODO: handle user updates... or it handled automatically?


@asynccontextmanager
async def history_middleware(update: Update, context: CustomContext):
    # TODO:
    # initialize crud in middleware and use in as func argument
    crud.append_history(
        context.session,
        update.effective_user,
        update.message,
    )
    yield


########################################################################################
# TMP EXAMPLES
########################################################################################


@asynccontextmanager
async def layer_1(update, context):
    print('in layer 1')
    yield
    print('out layer 1')


@asynccontextmanager
async def layer_2(update, context):
    print('in layer 2')
    yield
    print('out layer 2')


@asynccontextmanager
async def layer_3(update, context):
    print('in layer 2')
    yield
    print('out layer 2')
