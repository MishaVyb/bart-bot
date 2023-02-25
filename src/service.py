from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from telegram._message import Message

from accessories import MediaType
from configurations import logger
from database import MessageModel
from database.models import UserModel
from exceptions import NoPhotosException


@dataclass
class AppService:
    session: AsyncSession
    user: UserModel
    """Effective user from DB (accessing telegram object via `user.tg`). """
    message: Message
    """Message from telegram update. """

    def append_history(self, message: Message):
        media_id = None
        media_type = None

        if message.photo:
            media_id = message.photo[-1].file_id
            media_type = MediaType.photo.value
        elif message.video:
            raise NotImplementedError

        instance = MessageModel(
            user_id=self.user.id,
            message_id=message.message_id,
            media_id=media_id,
            media_type=media_type,
            media_group_id=message.media_group_id,
            raw=message.to_dict(),
        )

        logger.debug(f'Append {instance} to history. ')
        self.session.add(instance)
        return instance

    async def get_media_id(self, *, media_type: MediaType | None = None):
        query = self._get_media_query(media_type)
        try:
            message = (await self.session.execute(query)).scalar_one()
        except NoResultFound:
            raise NoPhotosException()

        assert message.media_id
        return message.media_id

    async def get_media_count(self, *, media_type: MediaType | None = None):
        query = self._get_media_query(media_type)
        return len((await self.session.execute(query)).all())  # FIXME: check exists (or count)

    def _get_media_query(self, media_type: MediaType | None = None):
        types = [media_type.value] if media_type else [MediaType.photo.value, MediaType.video.value]
        return select(MessageModel).filter(
            MessageModel.user_id == self.user.storage,
            MessageModel.media_type.in_(types),
            MessageModel.media_id.isnot(None),
        )
