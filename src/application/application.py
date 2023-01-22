from types import NoneType

from telegram.ext import ContextTypes

from application.base import LayeredApplication
from application.context import CustomContext
from application.middlewares import (
    history_middleware,
    session_middleware,
    user_middleware,
)
from configurations import CONFIG


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
