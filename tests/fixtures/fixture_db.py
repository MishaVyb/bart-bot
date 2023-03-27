import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy_utils import create_database, database_exists, drop_database

from configurations import AppConfig
from database import BaseModel
from tests.conftest import logger


@pytest.fixture(scope='session')
def engine(config: AppConfig):
    return create_async_engine(config.db_url, echo=config.sql_logs, echo_pool=config.sql_logs)


@pytest.fixture(scope='session')
async def setup_database(engine: AsyncEngine):
    url = engine.url.set(drivername='postgresql+psycopg2')

    logger.debug(f'Set up test database: {url}. ')
    create_database(url)

    yield
    logger.debug(f'Tear down test database: {engine.pool.status()}. ')

    if database_exists(url):
        drop_database(url)


@pytest.fixture(scope='function')
async def setup_tables(engine: AsyncEngine, setup_database: None):
    async with engine.begin() as connection:
        # TODO create tables by alembic
        await connection.run_sync(BaseModel.metadata.create_all)

    yield
    await engine.dispose()

    try:
        async with engine.begin() as connection:
            await connection.run_sync(BaseModel.metadata.drop_all)
    except Exception as e:  # FIXME # deadlock error occurs sometimes
        logger.error(e)


@pytest.fixture
async def session(engine: AsyncEngine, setup_tables: None):
    async with AsyncSession(engine) as session, session.begin():
        yield session
