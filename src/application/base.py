from contextlib import AsyncContextDecorator
from typing import Callable, TypeAlias

from telegram import Update
from telegram.ext import Application, BaseHandler, CommandHandler, ExtBot, JobQueue

from application.context import CustomContext
from configurations import logger


class APPHandlers(list[BaseHandler]):
    """
    Handlers regestry.
    """

    def command(self, command=None, filters=None, block=True):
        def decorator(wrapped: Callable):
            self.append(
                CommandHandler(callback=wrapped, command=command or wrapped.__name__, filters=filters, block=block)
            )

            # NOTE
            # why returning the same function
            return Callable

        return decorator

    def append(self, handler: BaseHandler) -> None:
        logger.debug(f'Add <{handler.callback.__name__}> handler to registry. ')
        return super().append(handler)


MiddlewaresType: TypeAlias = list[Callable[[Update, CustomContext], AsyncContextDecorator]]

# TODO rename to ???
class LayeredApplication(Application[ExtBot[None], CustomContext, None, None, None, JobQueue]):
    _middlewares: list[Callable[[Update, CustomContext], AsyncContextDecorator]] = []

    def add_middlewares(self, middlewares: MiddlewaresType):
        if self._middlewares:
            raise RuntimeError('Middlewares already set.')

        self._middlewares = list(middlewares)

    def add_handlers(self, handlers, group=0) -> None:  # TODO annotations here and below!!
        if isinstance(handlers, dict):
            raise NotImplementedError

        for handler in handlers:
            handler.callback = self._handler_factory(handler.callback)

        super().add_handlers(handlers)

    def _handler_factory(self, handler: Callable):
        async def handler_caller(update, context):
            wrapped = self._wrap_into_middlewares(handler, update, context)

            await wrapped(update, context)  # unwrap (call for) one layer after another

        return handler_caller

    def _wrap_into_middlewares(self, handler: Callable, update, context):
        """
        Wrap handler into middlewares.
        """
        layer = handler  # variable alias to avoid Unbound error

        # - all middlewares wrapped into @asynccontextmanager
        # - @asynccontextmanager produce a decorator, which called with `layer` argument
        # - reversed: the last layer added will be called first when `handler_caller` invokes unwrapping
        for middleware in reversed(self._middlewares):
            layer = middleware(update, context)(layer)

        return layer
