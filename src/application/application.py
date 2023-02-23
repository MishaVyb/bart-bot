import logging
from types import NoneType

import sqlalchemy
from telegram.ext import ContextTypes

from application.base import LayeredApplication
from application.context import CustomContext
from application.handlers import handler
from application.middlewares import (
    history_middleware,
    session_middleware,
    user_middleware,
)
from configurations import CONFIG, logger

logger = logging.getLogger(__name__)


async def post_init(app: LayeredApplication):
    logger.info('post init called')
    app.add_middlewares(
        [
            session_middleware,
            user_middleware,
            history_middleware,
        ]
    )
    app.add_handlers(handler)
    app.add_error_handler(error_handler)


NoneContextType = ContextTypes(  # in-memory data is deprecated for our app
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
    .post_init(post_init)
)
app: LayeredApplication = builder.build()


async def error_handler(update: object, context: CustomContext) -> None:
    # UNUSED
    if isinstance(context.error, sqlalchemy.exc.IntegrityError):
        logger.error(f'IntegrityError: {context.error}')

    else:
        logger.error('')
        logger.error(
            '\n\n------------------------------------------------------------------'
            '\n[Exception while handling an update] ',
            exc_info=context.error,
        )
