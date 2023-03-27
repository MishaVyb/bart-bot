import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from telegram.ext import Application

from tests.conftest import TestConfig
from tests.tools.integration import ClientIntegration


@pytest.fixture(scope='session')
async def vybornyy_context(config: TestConfig, application: Application):
    """user #1 with tag `vybornyy`"""
    vybornyy = ClientIntegration(app=application, config=config)
    async with vybornyy.session_context('vybornyy'):
        yield vybornyy


@pytest.fixture
async def vybornyy(vybornyy_context: ClientIntegration, session: AsyncSession):
    vybornyy_context.db_session = session
    yield vybornyy_context
    vybornyy_context.db_session = None


@pytest.fixture(scope='session')
async def herzog_context(config: TestConfig, application: Application):
    """user #2 with tag `herzog`"""
    herzog = ClientIntegration(app=application, config=config)
    async with herzog.session_context('herzog'):
        yield herzog


@pytest.fixture
async def herzog(herzog_context: ClientIntegration, session: AsyncSession):
    herzog_context.db_session = session
    yield herzog_context
    herzog_context.db_session = None


@pytest.fixture(scope='session')
async def frusciante_context(config: TestConfig, application: Application):
    """user #3 with tag `frusciante`"""
    frusciante = ClientIntegration(app=application, config=config)
    async with frusciante.session_context('frusciante'):
        yield frusciante


@pytest.fixture
async def frusciante(frusciante_context: ClientIntegration, session: AsyncSession):
    frusciante_context.db_session = session
    yield frusciante_context
    frusciante_context.db_session = None
