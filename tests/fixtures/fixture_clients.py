import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from telegram.ext import Application

from tests.conftest import TestConfig
from tests.tools.integration import ClientIntegration


@pytest.fixture(scope='session')
async def vybornyy_context(config: TestConfig, application: Application):
    vybornyy = ClientIntegration(app=application, config=config)
    async with vybornyy.session_context('vybornyy'):
        yield vybornyy


@pytest.fixture
async def vybornyy(vybornyy_context: ClientIntegration, session: AsyncSession):
    vybornyy_context.db_session = session
    yield vybornyy_context
    vybornyy_context.db_session = None
