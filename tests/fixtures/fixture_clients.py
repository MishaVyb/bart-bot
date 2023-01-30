import pytest
from sqlalchemy.orm import Session
from telegram.ext import Application

from tests.conftest import ClientIntegration, TestConfig

# TODO: move to config!
#
# def phonenumber_generator(
#     *, amount: int = 100, prefix: int = 99966, DC: int = 1, suffix_interval: tuple[int, int] = [1000, 9999]
# ):

#     # use reserved numbers
#     yield '9996612048'

#     # generate random and *uniq* numbers
#     suffixes: set[int] = set()
#     while len(suffixes) < amount:
#         suffixes.add(random.randint(*suffix_interval))

#     while True:
#         yield f'{prefix}{DC}{suffixes.pop()}'


# DC = 1
# PHONE_NUMBERS_GENERATOR = phonenumber_generator(DC=DC)
# CONFIRMATION_CODE = f'{DC}' * 5


@pytest.fixture(scope='session')
async def vybornyy_context(config: TestConfig, application: Application):
    vybornyy = ClientIntegration(app=application, config=config)
    async with vybornyy.context('vybornyy'):
        yield vybornyy


@pytest.fixture
async def vybornyy(vybornyy_context: ClientIntegration, session: Session):
    vybornyy_context.db_session = session
    yield vybornyy_context
    vybornyy_context.db_session = None
