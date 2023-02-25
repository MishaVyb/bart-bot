from __future__ import annotations

from typing import ClassVar

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from telegram import User

from accessories import MediaType
from database.base import BaseModel


class UserModel(BaseModel):
    tg: User

    storage: Mapped[int]
    history: Mapped[list[MessageModel]] = relationship(backref='user', default_factory=list, repr=False)


class MessageModel(BaseModel):
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: ClassVar[UserModel]  # ORM relationship property from backref # ???

    message_id: Mapped[int]  # telegram has NOT uniq message ids for different chats, so it could not by used as PK
    media_id: Mapped[str | None] = mapped_column(repr=False)
    media_type: Mapped[MediaType | None]
    media_group_id: Mapped[str | None]

    raw: Mapped[dict] = mapped_column(repr=False)
