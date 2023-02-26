import logging
import random
import string

import pytest
from pyrogram import Client, filters  # type: ignore [attr-defined]

from configurations import AppConfig

logger = logging.getLogger(__name__)
logger.setLevel('INFO')
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s [%(filename)s]: %(message)s'))
    logger.addHandler(handler)


pytest_plugins = [
    'tests.fixtures.fixture_application',
    'tests.fixtures.fixture_clients',
    'tests.fixtures.fixture_config',
    'tests.fixtures.fixture_db',
    'tests.fixtures.fixture_images',
]


# UNUSED
# @pytest.fixture(scope="session")
# def event_loop():
#     # by default pytest-asyncio define 'event_loop' as function scoped fixture
#     # but we need it with session scope
#     return asyncio.get_event_loop()


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


class TestConfig(AppConfig):
    api_id: int
    api_hash: str
    strict_mode: bool

    username_postfix_len: int = 4
    integration_timeout_sec: float = 2.0

    _phonenumbers: set[str] = {'9996612048'}
    _dc_number: int = 1

    def get_phonenumber(self):
        return self._phonenumbers.pop()  # FIXME

    def get_confirmation_code(self):
        return str(self._dc_number) * 5

    def get_username(self, tag: str):
        postfix = ''.join(random.choice(string.ascii_lowercase) for _ in range(self.username_postfix_len))
        return tag + postfix


# FIXME make those fixture to be called before any other
@pytest.fixture(autouse=True, scope='function')
def aaa_new_line_function():
    """
    Fixture simple makes new line to separate each test logging output.
    """
    print()
    logger.debug('[start test function scope]')
    yield
    logger.debug('[end test function scope]')
    print()


@pytest.fixture(autouse=True, scope='session')
def aaa_new_line_session():
    """
    Fixture simple makes new line to separate each test logging output.
    """
    print()
    logger.debug('[start test session scope]')
    yield
    logger.debug('[end test session scope]')
    print()
