import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import selectinload
from telegram import User

from database.models import StorageModel, UserModel

pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures('setup_tables')]


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
            user.tg

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


async def test_storage_relationships_loadings(session: AsyncSession, seed_users_with_relationships: None):
    options = (
        selectinload(UserModel.storage).selectinload(StorageModel.requests),
        selectinload(UserModel.storage).selectinload(StorageModel.participants),
    )
    vybornyy, herzog, frusciante = (await session.execute(select(UserModel).options(*options))).scalars().all()

    # check loadings
    assert vybornyy.storage == herzog.storage
    assert vybornyy.storage != frusciante.storage
    assert vybornyy.storage == frusciante.storage_request

    assert vybornyy.storage.participants == [vybornyy, herzog]
    assert vybornyy.storage.requests == [frusciante]

    assert frusciante.storage_request.participants == [vybornyy, herzog]
    assert frusciante.storage_request.requests == [frusciante]


async def test_storage_relationships_adding(engine: AsyncEngine, seed_users_with_relationships: None):
    options = (
        selectinload(UserModel.storage).selectinload(StorageModel.requests),
        selectinload(UserModel.storage).selectinload(StorageModel.participants),
        selectinload(UserModel.storage_request).selectinload(StorageModel.requests),
        selectinload(UserModel.storage_request).selectinload(StorageModel.participants),
    )
    async with AsyncSession(engine) as session, session.begin():
        vybornyy, herzog, frusciante = (await session.execute(select(UserModel).options(*options))).scalars().all()

        # act:
        participant = vybornyy.storage.requests.pop()
        vybornyy.storage.participants += [participant]

        # NOTE: raw sql:
        # UPDATE "user" SET storage_id=1, storage_request_id=None, updated_at=now() WHERE "user".id = 3

    async with AsyncSession(engine) as session, session.begin():
        vybornyy, herzog, frusciante = (await session.execute(select(UserModel).options(*options))).scalars().all()

        # check storage owner:
        assert vybornyy.storage.participants == [vybornyy, herzog, frusciante]
        assert vybornyy.storage.requests == []

        # check new participant:
        assert frusciante.storage == vybornyy.storage
        assert frusciante.storage_request == None
