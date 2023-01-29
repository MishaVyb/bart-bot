import pytest

from application.application import NoneContextType, post_init
from application.base import LayeredApplication
from configurations import AppConfig, logger
from tests.conftest import logger


@pytest.fixture(autouse=True)
async def application(config: AppConfig):
    builder = (
        LayeredApplication.builder()
        #
        # PTB does not have native support for Telegram Test environment.
        # But it could be handled by adding '/test' suffix to Bot token.
        #
        # Issue: https://github.com/python-telegram-bot/python-telegram-bot/issues/3355
        .token(config.bot_token.get_secret_value() + '/test')
        .context_types(NoneContextType)
        .application_class(LayeredApplication)
        .post_init(post_init)
    )

    app: LayeredApplication = builder.build()

    await app.initialize()  # initialize Does *not* call `post_init` - that is only done by run_polling/webhook
    await app.post_init(app)
    await app.start()

    logger.info('Stat app polling... ')
    await app.updater.start_polling()

    yield app

    logger.info('Stop app polling... ')
    await app.updater.stop()
    await app.stop()
    await app.shutdown()
