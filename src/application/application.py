from types import NoneType

from telegram.ext import ContextTypes

from application.base import LayeredApplication
from application.context import CustomContext
from application.handlers import handler
from application.middlewares import (
    args_middleware,
    history_middleware,
    service_middleware,
    session_middleware,
    user_middleware,
)
from configurations import CONFIG, logger


async def app_init(app: LayeredApplication):
    logger.info('App post init. ')
    app.add_middlewares(
        [
            session_middleware,
            user_middleware,
            service_middleware,
            history_middleware,
            args_middleware,
        ]
    )
    app.add_handlers(list(handler.values()))  # FIXME
    app.add_error_handler(error_handler)


NoneContextType = ContextTypes(  # in-memory data is deprecated for this application
    user_data=NoneType,
    chat_data=NoneType,
    bot_data=NoneType,
    context=CustomContext,
)

# TODO create appbuilder object, but do not create app
builder = (
    LayeredApplication.builder()
    .token(CONFIG.bot_token.get_secret_value())
    .context_types(NoneContextType)
    .application_class(LayeredApplication)
    .post_init(app_init)
)
app: LayeredApplication = builder.build()


async def error_handler(update: object, context: CustomContext) -> None:
    logger.error(
        f'[Exception while handling an update] {context.error}. Full traceback: \n'
        '---------------------------------------------------------------------\n\n',
        exc_info=context.error,
    )
