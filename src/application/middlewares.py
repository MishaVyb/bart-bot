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
from telegram import Update

from application.context import CustomContext
from configurations import CONFIG, logger
from database import crud
from database.models import UserModel


@asynccontextmanager
async def session_context():
    # ??? define engine in scope for every update or globally for all app only once in beginnings
    #
    engine = create_async_engine(CONFIG.db_uri(), echo=CONFIG.sql_logs)
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
    await engine.dispose()


@asynccontextmanager
async def session_middleware(update: Update, context: CustomContext):
    async with session_context() as session:
        setattr(context, 'session', session)
        yield
        try:
            delattr(context, 'session')
        except Exception:
            logger.error(f'Delleting session attr failed. ')  # FIXME


@asynccontextmanager
async def user_middleware(update: Update, context: CustomContext):
    context.db_user = await crud.get_or_create(
        context.session,
        UserModel,
        id=update.effective_user.id,
        extra_kwargs={'storage': update.effective_user.id},  # set default storage
    )

    yield
    #
    # TODO: save orm user updates... or it handled by alchemy automatically?


@asynccontextmanager
async def logging_middleware(update: Update, context: CustomContext):
    # TODO
    yield


@asynccontextmanager
async def history_middleware(update: Update, context: CustomContext):
    # TODO:
    # initialize crud (Service) in middleware and use in as func argument
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
