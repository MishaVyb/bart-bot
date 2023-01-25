import pytest

from configurations import AppConfig, logger

__all__ = ['logger']

pytest_plugins = [
    'tests.fixtures.fixture_application',
    'tests.fixtures.fixture_clients',
    'tests.fixtures.fixture_config',
    'tests.fixtures.fixture_db',
]


class TestConfing(AppConfig):
    api_id: int
    api_hash: str


TEST_CONFIG = TestConfing(_env_file='test.env')


@pytest.fixture(autouse=True)
def new_line():
    """
    Fixture simple makes new line to separate each test logging output.
    """
    print()
    yield
    print()
