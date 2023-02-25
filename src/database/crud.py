from typing import Type, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from telegram._message import Message
from telegram._user import User
from accessories import MediaType

from configurations import logger
from database import BaseModel, MessageModel
from exceptions import NoPhotosException

# TODO rename to class BartService and to file service.py


def append_history(session: AsyncSession, effective_user: User, message: Message):

    # TODO discard "raw" column (create all fields for message object)
    #
    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = MediaType.photo.value
    elif message.video:
        raise NotImplementedError
    else:
        media_id = None
        media_type = None

    instance = MessageModel(
        user_id=effective_user.id,
        message_id=message.message_id,
        media_id=media_id,
        media_type=media_type,
        media_group_id=message.media_group_id,
        raw=message.to_dict(),
    )

    logger.debug(f'Append {instance} to history. ')
    session.add(instance)
    return instance


async def get_media_id(session: AsyncSession, storage: int, typ: MediaType | None = None):
    types = [typ.value] if typ else [MediaType.photo.value, MediaType.video.value]

    query = select(MessageModel).filter(
        MessageModel.user_id == storage, MessageModel.media_type.in_(types), MessageModel.media_id.isnot(None)
    )
    try:
        message = (await session.execute(query)).scalar_one()
    except NoResultFound:
        raise NoPhotosException()

    assert message.media_id
    return message.media_id


async def get_media_count(session: AsyncSession, storage: int, typ: MediaType | None = None):
    types = [typ.value] if typ else [MediaType.photo.value, MediaType.video.value]

    query = select(MessageModel).filter(
        MessageModel.user_id == storage, MessageModel.media_type.in_(types), MessageModel.media_id.isnot(None)
    )

    return len((await session.execute(query)).all())  # FIXME: check exists (or count)


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
