from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import BaseModel


class UserModel(BaseModel):
    storage: Mapped[int]
    history: Mapped[list[MessageModel]] = relationship(backref='user', default_factory=list)


# class UserPropertyMixin:  # TODO declarative mixin and rename to UserRelationMixin
#     """
#     Shortcut for having:

#     >>> user_id: int = Column(..)   # foreign key
#     >>> user: UserModel             # annotation for UserModel's relationship backref
#     """

#     __abstract__ = True

#     user: Mapped[UserModel]

#     @declared_attr
#     def user_id(self) -> Mapped[int]:
#         return Column(BigInteger, ForeignKey('users.id'), nullable=False)


class MessageModel(BaseModel):
    """Raw"""

    # tg_id: Mapped[int] = Column(nullable=False, unique=False)
    # """
    # Telegram defined id. It counts every message from user and bot for each chat separately from others.
    # Therefore `unique=False`.
    # """

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    raw: Mapped[dict] = mapped_column()
