from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import filters

from application.base import APPHandlers
from application.context import CustomContext
from configurations import logger
from content import CONTENT
from database import crud
from exceptions import NoPhotosException

handler = APPHandlers()


@handler.command()
async def start(update: Update, context: CustomContext) -> None:
    await update.message.reply_text(
        text=CONTENT.messages.start.format(username=update.effective_user.username),
        reply_markup=ReplyKeyboardMarkup(CONTENT.keyboard, resize_keyboard=True),
    )


@handler.message()
async def photo(update: Update, context: CustomContext) -> None:
    if (await crud.get_media_count(context.session, context.db_user.storage)) > 1:
        await update.message.reply_text(text=CONTENT.messages.receive_photo.basic.get())
    else:
        await update.message.reply_text(text=CONTENT.messages.receive_photo.initial.get())


@handler.message(filters.Regex(r'|'.join(CONTENT.buttons)))
async def emoji_food(update: Update, context: CustomContext) -> None:
    try:
        photo = await crud.get_media_id(context.db_user.storage)
    except NoPhotosException as e:
        logger.debug(e)
        await update.message.reply_text(CONTENT.messages.exceptions.no_photos)
    else:
        await update.message.reply_photo(photo, CONTENT.messages.send_photo.any.get())


@handler.message()
async def all(update: Update, context: CustomContext) -> None:
    await update.message.reply_text(text=CONTENT.messages.regular.get())
