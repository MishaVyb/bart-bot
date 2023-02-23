import pytest
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from configurations import AppConfig
from database.models import UserModel
from tests.conftest import ClientIntegration

pytestmark = pytest.mark.anyio


async def test_user_middleware(vybornyy: ClientIntegration, config: AppConfig, session: AsyncSession):

    # no user at DB before act:
    with pytest.raises(NoResultFound):
        await vybornyy.db_user

    async with vybornyy.collect(amount=1):
        await vybornyy.client.send_message(config.botname, '/start')

    # user appears at DB:
    assert await vybornyy.db_user


async def test_history_middleware(vybornyy: ClientIntegration, config: AppConfig):
    text = f'hey from {vybornyy.tg_user.username}'
    async with vybornyy.collect(timeout=0):
        message = await vybornyy.client.send_message(config.botname, '/start')
        message = await vybornyy.client.send_message(config.botname, text)

    history = (await vybornyy.db_user).history
    assert len(history) == 2
    assert history[-1].raw['text'] == text
    assert history[-1].raw['text'] == message.text

    # NOTE
    # it seems really wired, but the same message has different ids for user client and for bot
    with pytest.raises(AssertionError):
        assert history[-1].raw['message_id'] == message.id
