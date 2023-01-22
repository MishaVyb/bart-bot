from telegram import ReplyKeyboardMarkup, Update

from application.application import app
from application.context import CustomContext
from configurations import logger
from content import CONTENT


@app.command()
async def start(update: Update, context: CustomContext) -> None:
    logger.debug('start handler in')

    await update.message.reply_text(
        text=CONTENT.messages.start.format(username=update.effective_user.username),  # type: ignore # FIXME
        reply_markup=ReplyKeyboardMarkup(CONTENT.keyboard, resize_keyboard=True),
    )

    logger.debug('start handler out')
