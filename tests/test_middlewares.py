import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from configurations import AppConfig
from tests.tools.integration import ClientIntegration

pytestmark = pytest.mark.anyio
# pytestmark = pytest.mark.usefixtures() # TODO


async def test_user_middleware(vybornyy: ClientIntegration, config: AppConfig, session: AsyncSession):
    # no user at DB before act:
    with pytest.raises(NoResultFound):
        await vybornyy.user

    # test action:
    async with vybornyy.collect(amount=1):
        await vybornyy.client.send_message(config.botname, '/start')

    # user appears at DB with tg user id:
    assert await vybornyy.user
    assert (await vybornyy.user).id == vybornyy.client.me.id


async def test_history_middleware(vybornyy: ClientIntegration, config: AppConfig):
    text = f'hey from {vybornyy.client.me.username}'
    async with vybornyy.collect():
        message = await vybornyy.client.send_message(config.botname, text)

    history = (await vybornyy.user).history
    assert len(history) == 1

    # NOTE
    # We could check messages ids, but the same message has different ids for User client and for Bot client.
    # Therefore we check identity by message text.
    with pytest.raises(AssertionError):
        assert history[-1].json['message_id'] == message.id
    assert history[-1].json['text'] == text
    assert history[-1].json['text'] == message.text
