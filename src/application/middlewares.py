"""
Module to describe application's middleware as context manager wrappers.

### Usage:

>>> @asynccontextmanager
>>> async def custom_middleware(update: Update, context: CustomContext):
>>>     # <setup>
>>>     try:
>>>         # <add some attrubutes to context>
>>>         yield
>>>     finally:
>>>         # <cleanup>

* and pass your middlewares to application then:

>>> app.add_middlewares([custom_middleware, ...])

### Yield value:

Only `yield None` is allowed, because `@asynccontextmanager` return help-object with `AsyncContextDecorator` in bases.
Its `__call__` method is used to wrap handler into defined middleware. But __call__ do nothing with yielded value and
it cannot be provided anyhow. So there is the reason to pass any values directly to `update` / `context`.

### Extended usage:

>>> class middleware_as_a_class():
>>>
>>>     def __init__(self, update: Update, context: CustomContext) -> None:
>>>         pass
>>>
>>>     def __call__(self, handler_callback: Callable):
>>>         async def inner(update: Update, context: CustomContext):
>>>             # Usual decorator implementation.
>>>             # Add some attrubutes to context / update or any other stuff.
>>>
>>>             # Call to wrapped function:
>>>             await handler_callback(**kwargs)
>>>
>>>             # Cleanup.
>>>
>>>         return inner
"""

import inspect
from contextlib import asynccontextmanager
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from telegram import Update

from application.context import CustomContext
from configurations import CONFIG, logger
from database.models import UserModel
from service import AppService
from utils import get_func_name, get_or_create


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
            logger.error('Delleting session attr failed. ')  # FIXME


@asynccontextmanager
async def user_middleware(update: Update, context: CustomContext):
    logger.info(f'in: {get_func_name()}')

    if not update.effective_user:
        raise ValueError

    context.user = await get_or_create(
        context.session,
        UserModel,
        id=update.effective_user.id,
        extra_kwargs={'storage': update.effective_user.id, 'tg': update.effective_user},  # set default storage
    )

    # in case user already exists at DB, `tg` was ignored and we assign it directly:
    if not hasattr(context.user, 'tg'):
        context.tg = update.effective_user

    yield
    logger.info(f'Out: {get_func_name()}')
    # TODO: save orm user updates... or it handled by alchemy automatically?


@asynccontextmanager
async def logging_middleware(update: Update, context: CustomContext):
    # TODO
    yield


@asynccontextmanager
async def service_middleware(update: Update, context: CustomContext):
    context.service = AppService(context.session, context.user, update.message)
    yield


@asynccontextmanager
async def history_middleware(update: Update, context: CustomContext):
    context.service.append_history(update.message)
    yield


class args_middleware:  # noqa: N801
    def __init__(self, update: Update, context: CustomContext) -> None:
        pass

    def __call__(self, handler_callback: Callable):
        async def inner(update: Update, context: CustomContext):
            kwargs = self.get_handler_kwargs(handler_callback, update, context)
            return await handler_callback(**kwargs)

        return inner

    @classmethod
    def get_handler_kwargs(cls, handler_callback: Callable, update: Update, context: CustomContext):
        signature = inspect.signature(handler_callback)
        kwargs = {}
        for param in signature.parameters.values():
            param.name
            if param.name == 'update':
                kwargs[param.name] = update
            elif param.name == 'context':
                kwargs[param.name] = context
            else:
                if hasattr(update, param.name):
                    kwargs[param.name] = getattr(update, param.name)
                elif hasattr(context, param.name):
                    kwargs[param.name] = getattr(context, param.name)
                else:
                    raise ValueError(f'Invalid handler argument ({param}). Signature missmatch for {handler_callback}.')

            if param.annotation is not param.empty and not isinstance(kwargs[param.name], param.annotation):
                raise TypeError(f'Invalid handler argument type ({param}). Signature missmatch for {handler_callback}.')

        return kwargs
