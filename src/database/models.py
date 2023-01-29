from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Column, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, relationship

from database.base import BaseModel


class UserModel(BaseModel):
    history: list[MessageModel] = relationship('database.models.MessageModel', backref='user')


class UserPropertyMixin:  # TODO declarative mixin and rename to UserRelationMixin
    """
    Shortcut for having:

    >>> user_id: int = Column(..)   # foreign key
    >>> user: UserModel             # annotation for UserModel's relationship backref
    """

    __abstract__ = True

    user: Mapped[UserModel]

    @declared_attr
    def user_id(self) -> Mapped[int]:
        return Column(BigInteger, ForeignKey('users.id'), nullable=False)


class MessageModel(BaseModel, UserPropertyMixin):
    """Raw"""

    message_id: Mapped[int] = Column(BigInteger, nullable=False, unique=False)
    """
    Telegram defined id. It counts every message from user and bot for each chat separately from others.
    Therefore `unique=False`.
    """

    raw: Mapped[dict] = Column(JSON, nullable=False)
