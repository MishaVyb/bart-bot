import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy_utils import create_database, database_exists, drop_database

from configurations import AppConfig
from database import BaseModel
from tests.conftest import logger


@pytest.fixture(scope='session')
def engine(config: AppConfig):
    return create_async_engine(config.db_uri(), echo=config.sql_logs, echo_pool=config.sql_logs)


@pytest.fixture(autouse=True, scope='session')
def setup_database(engine: AsyncEngine):
    logger.debug(f'Set up test database: {engine.url=}. ')

    url = engine.url.set(drivername='postgresql+psycopg2')
    if database_exists(url):
        logger.warning('Running tests against existing database is deprecated. All data will be gone. ')
        drop_database(url)

    create_database(url)

    yield
    logger.debug(f'Tear down test database: {engine.pool.status()}. ')

    if database_exists(url):
        drop_database(url)


@pytest.fixture(autouse=True, scope='function')
async def setup_tables(engine: AsyncEngine):
    async with engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.create_all)

    yield

    await engine.dispose()  # ???
    async with engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.drop_all)


@pytest.fixture
async def session(engine: AsyncEngine):
    async with AsyncSession(engine) as session, session.begin():
        yield session
