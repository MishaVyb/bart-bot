import pytest

from tests.conftest import ClientIntegration, TestConfig

TESTUSERS = ('vybornyy',)  # , 'simusik', 'barticheg'

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
async def integration(config: TestConfig):
    return ClientIntegration(config=config)


@pytest.fixture(scope='session')
async def vybornyy(integration: ClientIntegration):
    async with integration.context('vybornyy'):
        yield integration
