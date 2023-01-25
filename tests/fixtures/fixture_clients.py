import pytest
from conftest import TEST_CONFIG
from pyrogram import Client


@pytest.fixture
async def vybornyy():
    # NOTE:
    # Pyrogram authentication runs only once to create session file which will be used in father test runnings.
    # BartBot Tests build to be run on `test` Telegram environment. It has the same behavior, but complitely deferent
    # set of users, bot and conntent entirely.
    #
    # but running pytest from different shells (as macOS terminal or VSCode debugger) require to create .session file
    # in different direcotries (as venv/bin or venv/.../site-packages/pytest)

    app = Client('vybornyy', api_id=TEST_CONFIG.api_id, api_hash=TEST_CONFIG.api_hash, test_mode=True)
    async with app:
        yield app
