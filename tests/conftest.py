import logging

import pytest

from configurations import AppConfig

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s [%(filename)s:%(lineno)s] %(message)s'))
    logger.addHandler(handler)


pytest_plugins = [
    'tests.fixtures.fixture_application',
    'tests.fixtures.fixture_clients',
    'tests.fixtures.fixture_config',
    'tests.fixtures.fixture_db',
    'tests.fixtures.fixture_images',
    'tests.fixtures.fixture_users',
]


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


class TestConfig(AppConfig):
    api_id: int
    api_hash: str

    strict_mode: bool
    integration_timeout_sec: float = 2.0
    phonenumbers: set[str] = set()

    def get_phonenumber(self):
        return self.phonenumbers.pop() if self.phonenumbers else None


# FIXME make those fixture to be called before any other
@pytest.fixture(autouse=True, scope='function')
def new_line_function():
    """
    Fixture simple makes new line to separate each test logging output.
    """
    print()
    logger.debug('[start test function scope]')
    yield
    logger.debug('[end test function scope]')
    print()


@pytest.fixture(autouse=True, scope='session')
def new_line_session():
    """
    Fixture simple makes new line to separate each test logging output.
    """
    print()
    logger.debug('[start test session scope]')
    yield
    logger.debug('[end test session scope]')
    print()
