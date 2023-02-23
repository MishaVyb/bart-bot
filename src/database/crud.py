from typing import Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram._message import Message
from telegram._user import User

from configurations import logger
from database import BaseModel, MessageModel


def append_history(session: AsyncSession, effective_user: User, message: Message):
    logger.debug(f'Append {message} to history. ')

    # TODO discard "raw" column (create all fields for message object)
    #
    instance = MessageModel(user_id=effective_user.id, raw=message.to_dict())
    session.add(instance)
    return instance


async def get_photo_id(session: AsyncSession, storage: int):
    query = select(MessageModel).filter(
        MessageModel.user_id == storage,
        # TODO random and only with photo
    )
    message = (await session.execute(query)).scalar_one()
    return message.raw


_ModelType = TypeVar('_ModelType', bound=BaseModel)


async def get_or_create(
    session: AsyncSession,
    model: Type[_ModelType],
    extra_kwargs: dict = {},
    **instance_kwargs,
) -> _ModelType:
    """
    Get or create model instance if it does not exist.

    `instance_kwargs`: taking for quering DB
    `extra_kwargs`: taking for instance creation united with `instance_kwargs`
    """

    result = await session.execute(select(model).filter_by(**instance_kwargs))
    if instance := result.scalar():
        return instance

    instance_kwargs |= extra_kwargs
    instance = model(**instance_kwargs)
    session.add(instance)

    logger.info(f'{instance} added to database. ')
    return instance
