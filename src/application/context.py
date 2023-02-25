from sqlalchemy.ext.asyncio import AsyncSession
from telegram.ext import CallbackContext, ExtBot

from database.models import UserModel


class CustomContext(CallbackContext[ExtBot, None, None, None]):
    session: AsyncSession  # TODO rename db_session
    user: UserModel
