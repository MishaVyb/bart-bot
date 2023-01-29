from sqlalchemy.orm import Session

from configurations import AppConfig
from database.models import MessageModel
from tests.conftest import ClientIntegration


async def test_history_middleware(session: Session, vybornyy: ClientIntegration, config: AppConfig):
    vybornyy.db_session = session

    # TODO
    # add shortcut access to DB via ClientIntegration class
    initial_count = session.query(MessageModel).filter_by(user_id=vybornyy.tg_user.id).count()

    async with vybornyy.collect(amount=1) as messages:
        await vybornyy.client.send_message(config.botname, '/start')

    result_count = session.query(MessageModel).filter_by(user_id=vybornyy.tg_user.id).count()

    assert initial_count + 1 == result_count
