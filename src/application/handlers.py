import re
from asyncio import sleep

from telegram import Bot, Message, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, filters

from application.base import APPHandlers, LayeredApplication
from configurations import logger
from content import CONTENT
from database.models import MessageModel, UserModel
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
async def photo(message: Message, service: AppService, user: UserModel):
    if (await service.get_media_count()) > 1:
        # [1] many photos received:
        # reply in case it first Update with that media group
        if message.media_group_id:
            count = await service.get_history_count(MessageModel.media_group_id == message.media_group_id)
            if count <= 1:
                await message.reply_text(text=CONTENT.messages.receive_photo.group.get())
            return

        # [2] single photo received
        await message.reply_text(text=CONTENT.messages.receive_photo.basic.get())
        return

    # [3] photo received in a first time
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
async def family_start(
    bot: Bot, message: Message, service: AppService, user: UserModel, application: LayeredApplication
):
    """
    ### Add to family. Workflow.

    - User forward any other-user message to use his storage.
    - BartBot ask storage-owner for permition.
    - After confirmation is received, user associate with this storage.
    """

    if not user.tg.username:
        raise NotImplementedError

    try:
        from_user = await service.get_user(message.forward_from)
    except NoUserException:
        await message.reply_text(CONTENT.messages.exceptions.user_not_start_bot)
        return ConversationHandler.END

    if user.storage == from_user.storage:
        await message.reply_text(CONTENT.messages.exceptions.already_added_to_family)
        return ConversationHandler.END

    # NOTE: send an reqest for confirmation *NOT* to `from_user`, but to owner of the storage he is associated with
    await bot.send_message(from_user.storage.id, CONTENT.messages.family.request.format(username=user.tg.username))
    user.storage_request = from_user.storage

    # conversation routing
    family: ConversationHandler = handler['family']
    family_key = (from_user.storage.id,)
    if family_key in family._conversations:
        raise NotImplementedError

    family._update_state('making_response_for_family_request', family_key)
    return ConversationHandler.END


@handler.message(filters.Regex(re.compile(r'|'.join(CONTENT.confirm_answers), re.IGNORECASE)))
async def family_confirm(bot: Bot, message: Message, service: AppService, user: UserModel):
    if not user.storage.requests:
        logger.error('No family requests. ')
        return
    if len(user.storage.requests) > 1:
        logger.warning('Many family requests: not implemented. Taking the last. ')  # TODO

    participant = user.storage.requests.pop()
    user.storage.participants.append(participant)

    await bot.send_message(participant.id, CONTENT.messages.family.confirm)
    await message.reply_text(CONTENT.messages.family.confirm)

    return ConversationHandler.END


@handler.message(filters.Regex(re.compile(r'|'.join(CONTENT.reject_answers), re.IGNORECASE)))
async def family_reject(bot: Bot, message: Message, service: AppService, user: UserModel):
    if not user.storage.requests:
        logger.error('No family requests. ')
        return
    if len(user.storage.requests) > 1:
        logger.warning('Many family requests: not implemented. Taking the last. ')  # TODO

    participant = user.storage.requests.pop()
    await bot.send_message(participant.id, CONTENT.messages.family.reject)

    return ConversationHandler.END


@handler.message(filters.ALL)
async def family_fallback(message: Message):
    await message.reply_text(CONTENT.messages.exceptions.conversation_fallback)
    return ConversationHandler.END


handler.append(
    ConversationHandler(
        entry_points=[
            handler['family_start'],
        ],
        states={
            'making_response_for_family_request': [
                handler['family_confirm'],
                handler['family_reject'],
            ],
        },
        fallbacks=[
            handler['family_fallback'],
        ],
        per_chat=False,
        per_user=True,
        per_message=False,
    ),
    handler_name='family',
)

# FIXME
del handler['family_start']
del handler['family_confirm']
del handler['family_reject']
del handler['family_fallback']


@handler.message()
async def all(message: Message):
    await message.reply_text(text=CONTENT.messages.regular.get())
