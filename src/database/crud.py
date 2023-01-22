from typing import Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from configurations import logger
from database import BaseModel, MessageModel


def append_history(session: AsyncSession, user_id: int, message_id: int, message_raw: dict):
    session.add(
        MessageModel(user_id=user_id, id=message_id, raw=message_raw),
    )


_ModelType = TypeVar('_ModelType', bound=BaseModel)


def get_or_create(
    session: Session, model: Type[_ModelType], instance_kwargs: dict, extra_kwargs: dict = {}, *, echo: bool = False
) -> _ModelType:
    """
    Get or create model instance if it does not exist.

    `instance_kwargs`: taking for session query
    `extra_kwargs`: taking for instance creation united with `instance_kwargs`
    """
    instance = session.query(model).filter_by(**instance_kwargs).one_or_none()
    if instance:
        return instance

    instance_kwargs.update(extra_kwargs)
    instance = model(**instance_kwargs)
    session.add(instance)
    if echo:
        logger.info(f'{instance} added to database. ')

    return instance
