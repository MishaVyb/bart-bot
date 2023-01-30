from sqlalchemy.orm import Session

from configurations import AppConfig
from database.models import MessageModel, UserModel
from tests.conftest import ClientIntegration


async def test_user_middleware(vybornyy: ClientIntegration, config: AppConfig, session: Session):
    # [1] check that user added to DB after first message
    user_query = session.query(UserModel).filter_by(id=vybornyy.tg_user.id)
    assert user_query.one_or_none() is None

    async with vybornyy.collect(amount=1):
        await vybornyy.client.send_message(config.botname, '/start')

    assert user_query.one_or_none() is not None


async def test_history_middleware(vybornyy: ClientIntegration, config: AppConfig):

    async with vybornyy.collect(amount=1):
        message = await vybornyy.client.send_message(config.botname, '/start')

    assert len(vybornyy.db_user.history) == 1

    return
    assert vybornyy.db_user.history[-1].message_id == message.id  # FIXME
