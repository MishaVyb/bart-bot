import pytest
from conftest import logger
from telegram.ext import ContextTypes

from application.application import NoneContextType, post_init
from application.base import LayeredApplication
from application.context import CustomContext
from application.handlers import handler
from application.middlewares import (
    history_middleware,
    session_middleware,
    user_middleware,
)
from configurations import CONFIG, AppConfig, logger


@pytest.fixture(autouse=True)
async def application(config: AppConfig):
    logger.info('Stat app polling... ')
    builder = (
        LayeredApplication.builder()
        .token(config.bot_token.get_secret_value() + '/test')
        .context_types(NoneContextType)
        .application_class(LayeredApplication)
        .post_init(post_init)
    )

    app: LayeredApplication = builder.build()

    await app.initialize()  # initialize Does *not* call `post_init` - that is only done by run_polling/webhook
    await app.post_init(app)
    await app.start()
    await app.updater.start_polling()

    yield app

    logger.info('Stop app polling... ')
    await app.updater.stop()
    await app.stop()
    await app.shutdown()
