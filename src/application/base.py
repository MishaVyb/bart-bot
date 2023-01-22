from contextlib import AsyncContextDecorator
from typing import Callable, Type

from telegram import Update
from telegram.ext import Application, BaseHandler, CommandHandler
from telegram.ext._application import DEFAULT_GROUP

from application.context import CustomContext
from configurations import logger


class LayeredApplication(Application):
    middlewares: list[Callable[[Update, CustomContext], AsyncContextDecorator]] = []

    def command(self, command=None, filters=None, block=True, group: int = DEFAULT_GROUP):
        def decorator(wrapped: Callable):
            kwargs = dict(command=command or wrapped.__name__, filters=filters, block=block)
            return self._base_handler_decorator(wrapped, CommandHandler, handler_kwargs=kwargs, group=group)

        return decorator

    def _base_handler_decorator(
        self, callback: Callable, handler_class: Type[BaseHandler], *, handler_kwargs: dict, group: int = DEFAULT_GROUP
    ):
        # TODO refactoring: move to another class / module
        async def _multilayered_handler_callback(update, context):
            wrapped = callback

            # [1] wrap handler into middlewares
            for middleware in reversed(self.middlewares):
                # @asynccontextmanager produce a decorator, which called with `wrapped` argument
                wrapped = middleware(update, context)(wrapped)

            ...

            # [finally] call for multilayered handler
            await wrapped(update, context)

        logger.debug(f'Add <{callback.__name__}> handler. ')
        self.add_handler(handler_class(callback=_multilayered_handler_callback, **handler_kwargs), group)
