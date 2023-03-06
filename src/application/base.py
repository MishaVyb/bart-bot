from contextlib import AsyncContextDecorator
from typing import Callable, TypeAlias

from telegram import Bot, Update
from telegram.ext import (
    Application,
    BaseHandler,
    CommandHandler,
    ConversationHandler,
    ExtBot,
    JobQueue,
    MessageHandler,
)
from telegram.ext import filters as telegram_filters

from application.context import CustomContext
from configurations import logger


class APPHandlers(dict[str, BaseHandler]):
    """
    Handlers regestry. Alternative way for adding handlers to application.

    Docs: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#advanced-snippets
    """

    # TODO: type annotations
    def command(self, command=None, filters=None, block=True):
        def callback(wrapped: Callable):
            self.append(
                CommandHandler(
                    callback=wrapped,
                    command=command or wrapped.__name__,
                    filters=filters,
                    block=block,
                )
            )
            return wrapped

        return callback

    def message(self, filters=None, block=True):
        def callback(wrapped: Callable):
            self.append(
                MessageHandler(
                    callback=wrapped,
                    filters=filters or getattr(telegram_filters, wrapped.__name__.upper()),
                    block=block,
                )
            )
            return wrapped

        return callback

    def append(self, handler: BaseHandler, *, handler_name: str = '') -> None:
        handler_name = handler_name or handler.callback.__name__
        logger.debug(f'Add <{handler_name}> handler to registry. ')
        self[handler_name] = handler


MiddlewaresType: TypeAlias = list[Callable[[Update, CustomContext], AsyncContextDecorator]]


# TODO rename to ???
class LayeredApplication(Application[ExtBot[None], CustomContext, None, None, None, JobQueue]):
    _middlewares: MiddlewaresType = []

    def add_middlewares(self, middlewares: MiddlewaresType):
        if self._middlewares:
            raise RuntimeError('Middlewares already set.')

        self._middlewares = list(middlewares)

    def add_handlers(self, handlers: dict | list, group: int = 0) -> None:  # type: ignore
        if isinstance(handlers, dict):
            raise NotImplementedError

        for handler in handlers:
            if isinstance(handler, ConversationHandler):
                # FIXME
                conversation_handler = handler

                for entry_handler in conversation_handler._entry_points:
                    logger.debug(f'[Add <{entry_handler.callback.__name__}> handler] ')
                    entry_handler.callback = self._handler_callback_factory(entry_handler.callback)

                for key, state_handlers in conversation_handler._states.items():
                    for state_handler in state_handlers:
                        logger.debug(f'[Add <{state_handler.callback.__name__}> handler] ')
                        state_handler.callback = self._handler_callback_factory(state_handler.callback)

                for fallback_handler in conversation_handler._fallbacks:
                    logger.debug(f'[Add <{fallback_handler.callback.__name__}> handler] ')
                    fallback_handler.callback = self._handler_callback_factory(fallback_handler.callback)

            else:
                handler.callback = self._handler_callback_factory(handler.callback)

        super().add_handlers(handlers)

    def _handler_callback_factory(self, original_callback: Callable):
        async def handler_caller(update, context):
            logger.info(f'[Handler: <{original_callback.__name__}>] Handling update. ')

            wrapped = self._wrap_into_middlewares(original_callback, update, context)
            await wrapped(update, context)  # unwrap (call for) one layer after another

            logger.info(f'[Handler: <{original_callback.__name__}>] Done. ')

        return handler_caller

    def _wrap_into_middlewares(self, original_callback: Callable, update, context):
        """
        Wrap original_callback into middlewares.
        """
        layer = original_callback  # variable alias to avoid Unbound error

        # - all middlewares wrapped into @asynccontextmanager
        # - @asynccontextmanager produce a decorator, which called with `layer` argument
        # - reversed: the last layer added will be called first when `handler_caller` invokes unwrapping
        for middleware in reversed(self._middlewares):
            middleware_decorator = middleware(update, context)
            layer = middleware_decorator.__call__(layer)

        return layer


class ExtendedBot(Bot):
    async def send_message(self, *args, **kwargs):
        # TODO provide Session to bot object (in middleware)
        # and append history here
        return await super().send_message(*args, **kwargs)
