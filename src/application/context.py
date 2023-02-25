from sqlalchemy.ext.asyncio import AsyncSession
from telegram.ext import CallbackContext, ExtBot

from database.models import UserModel
from service import AppService


class CustomContext(CallbackContext[ExtBot, None, None, None]):
    session: AsyncSession  # TODO rename db_session
    user: UserModel
    """Effective user from DB (accessing telegram object via `user.tg`). """
    service: AppService
    """Application service. """
