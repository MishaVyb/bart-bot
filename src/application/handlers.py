from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import filters

from application.base import APPHandlers
from application.context import CustomContext
from configurations import logger
from content import CONTENT
from exceptions import NoPhotosException
from database import crud

handler = APPHandlers()


@handler.command()
async def start(update: Update, context: CustomContext) -> None:
    await update.message.reply_text(
        text=CONTENT.messages.start.format(username=update.effective_user.username),
        reply_markup=ReplyKeyboardMarkup(CONTENT.keyboard, resize_keyboard=True),
    )


@handler.message()
async def all(update: Update, context: CustomContext) -> None:
    await update.message.reply_text(
        text=CONTENT.messages.start.format(username=update.effective_user.username),
        reply_markup=ReplyKeyboardMarkup(CONTENT.keyboard, resize_keyboard=True),
    )


@handler.message(filters.Regex(r'|'.join(CONTENT.buttons)))
async def emoji_food(update: Update, context: CustomContext) -> None:
    try:
        await update.message.reply_photo(
            photo=await crud.get_photo_id(context.db_user.storage),
            caption=CONTENT.messages.send_photo.any,
        )
    except NoPhotosException as e:
        logger.debug(e)
        await update.message.reply_text(CONTENT.messages.exceptions.no_photos)
