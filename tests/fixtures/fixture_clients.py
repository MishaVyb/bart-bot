import builtins
import random

import pytest
from pyrogram import Client
from pyrogram.errors.exceptions import bad_request_400

from tests.conftest import TestConfig, UserIntegration, logger

TESTUSERS = ('vybornyy',)  # , 'simusik', 'barticheg'

# TODO: move to config
def phonenumber_generator(
    *, amount: int = 100, prefix: int = 99966, DC: int = 1, suffix_interval: tuple[int, int] = [1000, 9999]
):

    # use reserved numbers
    yield '9996612048'

    # generate random and *uniq* numbers
    suffixes: set[int] = set()
    while len(suffixes) < amount:
        suffixes.add(random.randint(*suffix_interval))

    while True:
        yield f'{prefix}{DC}{suffixes.pop()}'


DC = 1
PHONE_NUMBERS_GENERATOR = phonenumber_generator(DC=DC)
CONFIRMATION_CODE = f'{DC}' * 5


def patch_signup(first_name: str, last_name: str):
    def mock_input(prompt: str = ''):
        if 'Enter first name: ' == prompt:
            reply = first_name
            logger.debug(f'[mock input] {prompt} {reply}')
            return reply

        if 'Enter last name (empty to skip): ' == prompt:
            reply = last_name
            logger.debug(f'[mock input] {prompt} {reply}')
            return reply

        raise ValueError(prompt)

    def mock_print(*args, **kwargs):
        logger.debug(f'[mock output] {args} {kwargs}')

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(builtins, 'input', mock_input)
    monkeypatch.setattr(builtins, 'print', mock_print)
    return monkeypatch


@pytest.fixture
# TODO: add backoff factor for auth fails
async def vybornyy(config: TestConfig):
    username = 'vybornyy'
    credentials = {'first_name': f'{username}-first-name', 'last_name': f'{username}-last-name'}
    phone = next(PHONE_NUMBERS_GENERATOR)
    client = Client(
        f'{username}-test-client',
        api_id=config.api_id,
        api_hash=config.api_hash,
        test_mode=True,
        in_memory=True,
        phone_number=phone,
        phone_code=CONFIRMATION_CODE,
    )

    logger.info(f'Make test authorization with {phone=}')
    # NOTE: some phonenumbers are registered already, some other not.
    # to be sure, handle sign up action by patching std input
    patched_inout = patch_signup(**credentials)
    async with client:
        patched_inout.undo()  # FIXME

        try:
            await client.set_username(username)
        except bad_request_400.UsernameNotModified as e:
            logger.warning(e)

        await client.update_profile(**credentials)

        yield UserIntegration(
            client,
            user=await client.get_me(),
            target=config.botname,
        )

        await client.set_username(None)
