from __future__ import annotations


from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from telegram import User

from accessories import MediaType
from database.base import BackRef, BaseModel


class UserModel(BaseModel):
    tg: User

    storage_id: Mapped[int] = mapped_column(ForeignKey('storage.id'), init=False)
    storage_request_id: Mapped[int | None] = mapped_column(ForeignKey('storage.id'), init=False, default=None)

    storage: Mapped[StorageModel] = relationship(foreign_keys=[storage_id], init=False, backref='participants')
    storage_request: Mapped[StorageModel | None] = relationship(
        foreign_keys=[storage_request_id], init=False, default=None, backref='requests'
    )

    history: Mapped[list[MessageModel]] = relationship(backref='user', default_factory=list, repr=False)

    def __post_init__(self):
        """
        Creates default storage with id equals telegram user id.
        """
        telegram_id = self.tg.id
        default_storage = StorageModel(id=telegram_id)
        self.id = telegram_id
        self.storage_id = default_storage.id
        self.storage = default_storage


class StorageModel(BaseModel):
    participants: BackRef[UserModel]
    requests: BackRef[UserModel]


class MessageModel(BaseModel):
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: BackRef[UserModel]

    message_id: Mapped[int]  # telegram has NOT uniq message ids for different chats, so it could not by used as PK
    media_id: Mapped[str | None] = mapped_column(repr=False)
    media_type: Mapped[MediaType | None]
    media_group_id: Mapped[str | None]

    json: Mapped[dict] = mapped_column(repr=False)
    """Full message as it is. """
