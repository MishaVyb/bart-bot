from types import NoneType

from app.application import LayeredApplication
from telegram.ext import Application, BaseHandler, CommandHandler, ContextTypes
from telegram.ext._application import DEFAULT_GROUP

from application.middlewares import (
    history_middleware,
    session_middleware,
    user_middleware,
)
from configurations import CONFIG
from context import CustomContext


async def post_init(app: LayeredApplication):
    app.middlewares = [
        session_middleware,
        user_middleware,
        history_middleware,
    ]


NoneContextType = ContextTypes(  # in-memory data is deprecated for our app
    user_data=NoneType,
    chat_data=NoneType,
    bot_data=NoneType,
    context=CustomContext,
)

app: LayeredApplication = (  # TOTO generic annotations
    LayeredApplication.builder()
    .token(CONFIG.bot_token.get_secret_value())
    .context_types(NoneContextType)
    .application_class(LayeredApplication)
    .post_init(post_init)
    .build()
)
