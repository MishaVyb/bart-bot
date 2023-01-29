import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database

from configurations import AppConfig
from database import BaseModel
from tests.conftest import logger


@pytest.fixture(scope='session')
def engine(config: AppConfig):
    return create_engine(config.db_uri(dialect='psycopg2'), echo=config.sql_logs)


@pytest.fixture(autouse=True, scope='session')
def setup_database(engine: Engine):
    logger.debug(f'Set up test database: {engine.url=}. ')

    if database_exists(engine.url):
        logger.warning('Running tests against existing database is deprecated. All data will be gone. ')
        drop_database(engine.url)

    create_database(engine.url)

    yield
    logger.debug(f'Tear down test database: {engine.pool.status()}. ')

    if database_exists(engine.url):
        drop_database(engine.url)


@pytest.fixture(autouse=True, scope='function')
def setup_tables(engine: Engine):
    BaseModel.metadata.create_all(engine)
    yield
    engine.dispose()  # ???
    BaseModel.metadata.drop_all(engine)


@pytest.fixture
def session(engine: Engine):
    with Session(engine) as session, session.begin():
        yield session
