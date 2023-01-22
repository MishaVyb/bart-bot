from __future__ import annotations

from sqlalchemy import JSON, Column, ForeignKey, Integer
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Mapped, relationship

from database.base import BaseModel


class UserModel(BaseModel):
    history: list[MessageModel] = relationship('MessageModel', backref='user')


class UserPropertyMixin:
    __abstract__ = True

    user: Mapped[UserModel]

    @declared_attr
    def user_id(self) -> Mapped[int]:
        return Column(Integer, ForeignKey('users.id'), nullable=False)


class MessageModel(BaseModel, UserPropertyMixin):
    """Raw"""

    message_id: Mapped[int] = Column(Integer, nullable=False, unique=False)
    """
    Telegram defined id. It counts every message from user and bot for each chat separately from others.
    Therefore `unique=False`.
    """

    raw: Mapped[dict] = Column(JSON, nullable=False)
