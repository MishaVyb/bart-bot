from telegram import Update
from telegram.ext import ContextTypes

from configurations import logger


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = 'Hellow World!!!!!!'
    logger.debug('test debug log')
    logger.info('test info log')
    logger.warning('test warning log')
    logger.error('test error log')
    await update.message.reply_text(text=text)
