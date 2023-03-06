import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import selectinload
from telegram import User

from database.models import StorageModel, UserModel

pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures('setup_tables')]


@pytest.fixture
def tg_user():
    return User(1234, 'vybornyy', False)


async def test_user_model(engine: AsyncEngine, tg_user: User):

    # [1] check user creation and __post_init__
    async with AsyncSession(engine) as session, session.begin():
        user = UserModel(tg=tg_user)
        session.add(user)
        assert user.id == tg_user.id
        assert user.storage.id == tg_user.id
        assert user.storage_id == tg_user.id

    # [2] check user fetched from db
    async with AsyncSession(engine) as session, session.begin():
        query = (
            select(UserModel)
            .filter_by(id=tg_user.id)
            .options(
                selectinload(UserModel.storage),
            )
        )
        user = (await session.execute(query)).scalar_one()
        with pytest.raises(AttributeError, match=r"'UserModel' object has no attribute 'tg'"):
            str(user)

        # ORM know nothing about Telegram User and we must provided directly by hands:
        user.tg = tg_user

        # [3] check storage relationships
        query = (
            select(StorageModel)
            .filter_by(id=1234)
            .options(
                selectinload(StorageModel.participants),
                selectinload(StorageModel.requests),
            )
        )
        storage = (await session.execute(query)).scalar_one()
        assert storage.participants == [user]
        assert storage.requests == []
