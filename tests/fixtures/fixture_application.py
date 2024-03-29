import pytest

from application.application import NoneContextType, app_init
from application.base import LayeredApplication
from configurations import AppConfig
from tests.conftest import logger


@pytest.fixture(scope='session')
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
        .post_init(app_init)
    )

    app: LayeredApplication = builder.build()

    await app.initialize()  # initialize Does *not* call `post_init` - that is only done by run_polling/webhook
    await app.post_init(app)
    await app.start()

    logger.debug('Start test app polling... ')
    await app.updater.start_polling()

    yield app

    logger.debug('Stop test app polling... ')
    await app.updater.stop()
    await app.stop()
    await app.shutdown()
