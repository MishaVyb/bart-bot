import re
from asyncio import sleep

from telegram import Bot, Message, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, filters

from application.base import APPHandlers, LayeredApplication
from configurations import logger
from content import CONTENT
from database.models import UserModel
from exceptions import NoPhotosException, NoUserException
from service import AppService
from utils import get_func_name

handler = APPHandlers()


@handler.command()
async def start(user: UserModel, message: Message):
    logger.info(f'Call: {get_func_name()}')

    await message.reply_text(
        text=CONTENT.messages.start.format(username=user.tg.username or ''),
        reply_markup=ReplyKeyboardMarkup(CONTENT.keyboard, resize_keyboard=True),
    )


@handler.message()
async def photo(message: Message, service: AppService):
    if (await service.get_media_count()) > 1:
        await message.reply_text(text=CONTENT.messages.receive_photo.basic.get())
    else:
        await message.reply_text(text=CONTENT.messages.receive_photo.initial.get())


@handler.message(filters.Regex(r'|'.join(CONTENT.buttons)))
async def emoji_food(message: Message, service: AppService):
    await message.reply_text(CONTENT.messages.receive_food.get())
    await sleep(0.5)

    try:
        photo = await service.get_media_id()
    except NoPhotosException:
        await message.reply_text(CONTENT.messages.exceptions.no_photos)
    else:
        await message.reply_photo(photo, CONTENT.messages.send_photo.any.get())


@handler.message(filters.FORWARDED)
async def famely_start(
    bot: Bot, message: Message, service: AppService, user: UserModel, application: LayeredApplication
):
    """
    User forward any message to use his storage (add to famely).
    We ask storage owner for permition.
    And after confirmation is received, user associated with this storage.
    """
    logger.info(f'--------------> {get_func_name()}')

    if not user.tg.username:
        raise NotImplementedError

    try:
        from_user = await service.get_user(message.forward_from)
    except NoUserException:
        await message.reply_text(CONTENT.messages.exceptions.user_not_start_bot)
        return ConversationHandler.END

    if user.storage == from_user.storage:
        await message.reply_text(CONTENT.messages.exceptions.already_added_to_famely)
        return ConversationHandler.END

    # NOTE: send an reqest for confirmation *NOT* to `from_user`, but to owner of the storage he is associated with
    await bot.send_message(
        from_user.storage, CONTENT.messages.famely.request_for_adding_to_famely.format(username=user.tg.username)
    )

    famely: ConversationHandler = handler['famely']
    famely_key = (from_user.storage,)
    if famely_key in famely._conversations:
        raise NotImplementedError

    famely._update_state('making_response_for_famely_request', famely_key)
    return ConversationHandler.END


@handler.message(filters.Regex(re.compile(r'|'.join(CONTENT.confirm_answers), re.IGNORECASE)))
async def famely_confirm(bot: Bot, message: Message, service: AppService, user: UserModel):
    logger.info(f'--------------> {get_func_name()}')

    await bot.send_message()
    return ConversationHandler.END


@handler.message(filters.Regex(re.compile(r'|'.join(CONTENT.reject_answers), re.IGNORECASE)))
async def famely_reject(bot: Bot, message: Message, service: AppService, user: UserModel):
    logger.info(f'--------------> {get_func_name()}')
    return ConversationHandler.END


@handler.message(filters.ALL)
async def famely_fallback(bot: Bot, message: Message, service: AppService, user: UserModel):
    logger.info(f'--------------> {get_func_name()}')
    return ConversationHandler.END


handler.append(
    ConversationHandler(
        entry_points=[
            handler['famely_start'],
        ],
        states={
            'making_response_for_famely_request': [
                handler['famely_confirm'],
                handler['famely_reject'],
            ],
        },
        fallbacks=[
            handler['famely_fallback'],
        ],
        per_chat=False,
        per_user=True,
        per_message=False,
    ),
    handler_name='famely',
)

# FIXME
del handler['famely_start']
del handler['famely_confirm']
del handler['famely_reject']
del handler['famely_fallback']


@handler.message()
async def all(message: Message):
    await message.reply_text(text=CONTENT.messages.regular.get())
