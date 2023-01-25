from telegram import ReplyKeyboardMarkup, Update

from application.base import APPHandlers
from application.context import CustomContext
from configurations import logger
from content import CONTENT

handler = APPHandlers()


@handler.command()
async def start(update: Update, context: CustomContext) -> None:
    logger.debug('start handler in')

    await update.message.reply_text(
        text=CONTENT.messages.start.format(username=update.effective_user.username),  # type: ignore # FIXME
        reply_markup=ReplyKeyboardMarkup(CONTENT.keyboard, resize_keyboard=True),
    )

    logger.debug('start handler out')
