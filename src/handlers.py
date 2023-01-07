import random

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

import crud
from configurations import CONFIG, logger
from content import CONTENT
from exceptions import NoPhotosException


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # TODO: use custom data types, not dict
    #
    # SET APP DEFAULTS
    context.bot_data.setdefault('storages', {})

    # SET USER DEFAULTS
    default_storage = update.effective_user.id

    context.bot_data['storages'].setdefault(default_storage, {})
    context.bot_data['storages'][default_storage].setdefault('history', [])
    context.bot_data['storages'][default_storage].setdefault(
        'owner', update.effective_user.id
    )
    context.bot_data['storages'][default_storage].setdefault('sharings', [])

    context.user_data.setdefault('username', update.effective_user.username)  # shortcut
    context.user_data.setdefault('id', update.effective_user.id)  # shortcut
    context.user_data.setdefault('storage_id', default_storage)

    # TMP
    if update.effective_user.id in CONFIG.admin_sharings_ids:
        logger.debug(f'Taking {update.effective_user} to admin sharings. ')

        sharing_id = CONFIG.admin_id
        context.user_data['storage_id'] = sharing_id
        context.bot_data['storages'][sharing_id]['sharings'].append(
            update.effective_user.id
        )

    await update.message.reply_text(
        text=CONTENT.messages.start.format(username=update.effective_user.username),
        reply_markup=ReplyKeyboardMarkup(CONTENT.keyboard, resize_keyboard=True),
    )


async def admin_loaddata(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await crud.loaddata(context)


async def admin_flushdata(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raise NotImplementedError


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    # NOTE
    # storing only messages with photos
    await crud.update_history(update.message, context)

    # TODO
    # CONTENT.messages.receive_photo.initial
    await update.message.reply_text(random.choice(CONTENT.messages.receive_photo.basic))


# TODO: move to services.py, as it not telegram handler actually
async def send_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_photo(
            photo=await crud.get_photo_id(context),
            caption=CONTENT.messages.send_photo.any,
        )
    except NoPhotosException as e:
        logger.debug(e)
        await update.message.reply_text(CONTENT.messages.exceptions.no_photos)


async def receive_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(random.choice(CONTENT.messages.receive_food))
    await send_photo(update, context)


async def any_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(random.choice(CONTENT.messages.regular))
