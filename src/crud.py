import json
import random

from telegram import Bot, Message, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from configurations import CONFIG, logger
from content import CONTENT
from exceptions import NoPhotosException


async def loaddata(context: ContextTypes.DEFAULT_TYPE):
    """
    Upload messages from dump json file to user history storage.
    Usefull for data migration from previous application version.
    """
    bot, user, data = context.bot, context.user_data, context.bot_data
    with open(CONFIG.dump_filepath, 'r') as file:
        messages = json.loads(file.read())

    storage_id = user['storage_id']
    history: list = data['storages'][storage_id]['history']
    history += Message.de_list(messages, bot=bot)

    logger.debug(f'Successfully load history data. Total: {len(history)}. ')


async def update_history(message: Message, context: ContextTypes.DEFAULT_TYPE):
    bot, user, data = context.bot, context.user_data, context.bot_data

    storage_id = user['storage_id']
    history: list = data['storages'][storage_id]['history']
    history.append(message)

    logger.debug(f'Successfully add message to history. Total: {len(history)}. ')


async def get_photo_id(context: ContextTypes.DEFAULT_TYPE):
    bot, user, data = context.bot, context.user_data, context.bot_data
    logger.debug(f'Geting photo for {user}. ')

    storage_id = user['storage_id']
    history: list = data['storages'][storage_id]['history']
    if not history:
        raise NoPhotosException

    message = random.choice(data['storages'][storage_id]['history'])
    return next(reversed(message.photo)).file_id
