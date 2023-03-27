import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import selectinload
from telegram import User

from database.models import UserModel


@pytest.fixture
def tg_user():
    return User(1234, 'vybornyy', False)


@pytest.fixture
def tg_users():
    return [
        User(1, 'vybornyy', False),
        User(2, 'herzog', False),
        User(3, 'frusciante', False),
    ]


@pytest.fixture
async def seed_users(engine: AsyncEngine, tg_users: User):
    async with AsyncSession(engine) as session, session.begin():
        session.add_all([UserModel(tg=tg) for tg in tg_users])


@pytest.fixture
async def seed_users_with_relationships(engine: AsyncEngine, seed_users: None):
    """
    Family: vybornyy & herzog. One storage for both users. Owner: vybornyy
    Family request: frusciante. Make a request to join to vybornyy storage.
    """
    async with AsyncSession(engine) as session, session.begin():
        options = selectinload(UserModel.storage)
        vybornyy, herzog, frusciante = (await session.execute(select(UserModel).options(options))).scalars().all()

        # set
        herzog.storage = vybornyy.storage
        frusciante.storage_request = vybornyy.storage
