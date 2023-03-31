from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from telegram import User
from telegram._message import Message

from accessories import MediaType
from configurations import logger
from database import MessageModel
from database.models import StorageModel, UserModel
from exceptions import NoPhotosException, NoUserException


@dataclass
class AppService:
    """
    Database access implementation.
    """

    session: AsyncSession
    user: UserModel
    """Effective user from DB (accessing telegram object via `user.tg`). """
    message: Message
    """Message from telegram update. """

    async def get_user(self, user: User | int | None):
        """
        Get user from DB by `id` or Telegram `user.id`. User must have conversation with Bot.
        """
        if not user:
            raise ValueError(user)

        user_id = user.id if isinstance(user, User) else user
        options = (
            selectinload(UserModel.storage).selectinload(StorageModel.requests),
            selectinload(UserModel.storage).selectinload(StorageModel.participants),
        )
        query = select(UserModel).filter_by(id=user_id).options(*options)

        try:
            result = (await self.session.execute(query)).unique().scalar_one()
            if isinstance(user, User):
                result.tg = user
            return result
        except NoResultFound:
            raise NoUserException()

    def append_history(self, message: Message):
        media_id = None
        media_type = None

        if message.photo:
            media_id = message.photo[-1].file_id
            media_type = MediaType.photo.value
        elif message.video:
            logger.warn('Add video type. It is experemental future. ')
            media_id = message.video.file_id
            media_type = MediaType.video.value

        instance = MessageModel(
            user_id=self.user.id,
            message_id=message.message_id,
            media_id=media_id,
            media_type=media_type,
            media_group_id=message.media_group_id,
            json=message.to_dict(),
        )

        logger.debug(f'Append {instance} to history. ')
        self.session.add(instance)
        return instance

    async def get_media_id(self, *, media_type: MediaType | None = None):
        query = self._get_media_query(media_type).order_by(func.random()).limit(1)

        try:
            message = (await self.session.execute(query)).scalar_one()
        except NoResultFound:
            raise NoPhotosException()

        assert message.media_id
        return message.media_id

    async def get_media_count(self, *, media_type: MediaType | None = None):
        query = self._get_media_query(media_type)
        return len((await self.session.execute(query)).all())  # FIXME: SQL count

    def _get_media_query(self, media_type: MediaType | None = None):
        types = [media_type.value] if media_type else [MediaType.photo.value, MediaType.video.value]
        return select(MessageModel).filter(
            MessageModel.user_id.in_(participant.id for participant in self.user.storage.participants),
            MessageModel.media_type.in_(types),
            MessageModel.media_id.isnot(None),
        )

    async def get_history_count(self, *filters):
        query = select(MessageModel).filter(MessageModel.user_id == self.user.id, *filters)
        return len((await self.session.execute(query)).scalars().all())  # FIXME: SQL count
