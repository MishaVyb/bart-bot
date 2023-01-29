import pytest

from configurations import CONFIG, AppConfig
from tests.conftest import TestConfig, logger


@pytest.fixture(scope='session')
def config():
    return TestConfig(_env_file='test.env', botname='TestBartBot')


@pytest.fixture(scope='session', autouse=True)
def mock_config(config: AppConfig):
    """
    Patching collector config file and restore test files ('cities.json')
    """
    logger.debug(f'Pathing app configurations to those: {config}')

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(CONFIG.Config, 'allow_mutation', True)
        for field in AppConfig.__fields__:
            monkeypatch.setattr(CONFIG, field, getattr(config, field))

        monkeypatch.setattr(CONFIG.Config, 'allow_mutation', False)
        yield
