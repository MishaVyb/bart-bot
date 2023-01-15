from sqlalchemy.ext.asyncio import AsyncSession
from telegram.ext import CallbackContext, ExtBot


class CustomContext(CallbackContext[ExtBot, None, None, None]):
    session: AsyncSession
