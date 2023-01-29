from sqlalchemy.orm import Session

from configurations import AppConfig
from database.models import MessageModel
from tests.conftest import UserIntegration


async def test_history_middleware(session: Session, vybornyy: UserIntegration, config: AppConfig):

    # TODO
    # add shortcut access to DB via UserIntegration class
    initial_count = session.query(MessageModel).filter_by(user_id=vybornyy.user.id).count()

    async with vybornyy.integration(collect=1) as messages:
        await vybornyy.client.send_message(config.botname, '/start')

    result_count = session.query(MessageModel).filter_by(user_id=vybornyy.user.id).count()

    assert initial_count + 1 == result_count
