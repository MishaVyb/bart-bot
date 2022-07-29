from __future__ import annotations

import json
import logging
import os
import random
from datetime import datetime
import re
from time import sleep
from typing import Callable

from telegram import Bot, Chat, Message, ReplyKeyboardMarkup, Update, User
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)


import settings


############################################################

BOT = None


class UpdateMessageHandler:
    reply: str = ''

    def __init__(self, update: Update, context: CallbackContext) -> None:
        if (
            update.effective_chat is None
            or update.message is None
            or update.message.from_user is None
        ):
            raise ValueError

        self.update = update
        self.context = context

        self.chat: Chat = update.effective_chat
        self.message: Message = update.message
        self.user: User = update.message.from_user

    def __call__(self):
        raise NotImplementedError

    def send_message(self, **kwargs):
        try:
            if settings.DEBUG and not self.user_is_admin:
                logging.info(
                    f'Message {self.reply} to {self.user.username} won\'t be sent,'
                    f'because {settings.DEBUG=}'
                )
                return

            self.context.bot.send_message(
                chat_id=self.chat.id, text=self.reply, **kwargs
            )
        except BadRequest as e:
            logging.warning(f'BadRequest {e}')
            pass

    @property
    def user_is_admin(self) -> bool:
        return self.user.id == settings.ADMIN_CHAT_ID

    @classmethod
    def as_handler(cls, update: Update, context: CallbackContext):
        try:
            handler = cls(update, context)
        except ValueError as e:
            logging.warning(f"ValueError: {e.args}")
        else:
            handler()


class Start(UpdateMessageHandler):
    reply = "мяу, {name} 🐈‍⬛ загрузи сюда фотки, да побольше"
    buttons = ['🥛', '🍥', '🥟', '🍚', '🥓', '🍙', '🥖', '☕️', '🍣']
    sheldue = [
        datetime(
            year=2020,
            month=1,
            day=1,
            hour=7 - 3,
            minute=17,
            second=0,
        ),
        datetime(
            year=2020,
            month=1,
            day=1,
            hour=12 - 3,
            minute=53,
            second=0,
        ),
        datetime(
            year=2020,
            month=1,
            day=1,
            hour=19 - 3,
            minute=16,
            second=0,
        ),
    ]

    # sheldue message
    def callback(self, context: CallbackContext):
        self.reply = SheldueMessage.reply
        self.send_message()

    def __call__(self):

        # for time in self.sheldue:
        #     self.context.job_queue.run_daily(
        #         self.callback, context=self.chat.id, time=time
        #     )

        # now = datetime.now()
        # self.context.job_queue.run_daily(
        #     self.callback,
        #     context=self.chat.id,
        #     time=datetime(
        #         year=now.year,
        #         month=now.month,
        #         day=now.day,
        #         hour=now.hour,
        #         minute=now.minute,
        #         second=now.second + 5,
        #     ),
        # )
        self.reply = self.reply.format(name=self.user.name)
        self.send_message(
            reply_markup=(
                ReplyKeyboardMarkup(
                    [self.buttons[0:3], self.buttons[3:6], self.buttons[6:9]],
                    resize_keyboard=True,
                )
            ),
        )


class SendInfo(UpdateMessageHandler):
    reply = 'info: ' 'MessageHistory: ' 'count: {count}. ' 'all: {all}. '

    def __call__(self):
        # self.reply = self.reply.format(
        #     count=MessageHistory.objects.all().count(), all=MessageHistory.objects.all()
        # )
        self.send_message()


class GetPhoto(UpdateMessageHandler):
    reply = "мя"

    def __call__(self):
        pass

        # if not MessageHistory.objects.all().exists():
        #     self.reply = 'а где фотки?'
        #     self.send_message()
        #     return

        # message_history: MessageHistory = random.choice(MessageHistory.objects.all())
        # msg_str: str = message_history.message
        # msg_dict = json.loads(msg_str)
        # message: Message = Message.de_json(msg_dict, bot=BOT)

        # if message is None:
        #     error = f'Warning: message is None. {self=}'
        #     logging.warning(error)
        #     return

        # if not message.photo:
        #     error = f'Warning: not message.photo. {self=}'
        #     logging.warning(error)
        #     return

        # biggest_photo = next(reversed(message.photo))
        # photo_id = biggest_photo.file_id
        # self.send_message()
        # self.send_photo(photo_id)

    def send_photo(self, photo_id):
        try:
            if settings.DEBUG and not self.user_is_admin:
                logging.info(
                    f'Message {self.reply} to {self.user.username} won\'t be sent,'
                    f'because {settings.DEBUG=}'
                )
                return
            self.context.bot.send_photo(self.chat.id, photo_id)
        except BadRequest as e:
            logging.warning(f'BadRequest {e}')
            pass




# class CallbackMixin:

#     @classmethod
#     def as_callback(cls) -> CallbackMixin:
#         ...
#         return CallbackMixin()

#     # def __call__(self, CallbackContext):
#     #     context.bot.send_message(chat_id=self.chat.id, text=self.reply)


class SheldueMessage(UpdateMessageHandler):
    reply = f'я очень голодный, сейчас нашкодю!! покорми меня'

    def __call__(self):
        self.send_message()


class GetPhotoAfterFeeding(GetPhoto):
    reply = f'хрум хрум вкусненько'


class PutPhoto(UpdateMessageHandler):
    reply = f"спасибо, очень вкусно, мрррр"

    def __call__(self):
        # for not reapiting replys
        # for message_history in MessageHistory.objects.all():
        #     msg_str: str = message_history.message
        #     msg_dict = json.loads(msg_str)
        #     message: Message = Message.de_json(msg_dict, bot=BOT)
        #     if message.media_group_id == self.message.media_group_id:
        #         self.reply = ''

        # MessageHistory.objects.create(message=self.message.to_json())
        self.send_message()


class AnyMessage(UpdateMessageHandler):
    reply = "я кушал уже {count} раз{ending}, но этого не достаточно, хочу еще"

    def __call__(self):
        # count = MessageHistory.objects.all().count()
        # ending = ''
        # self.reply = self.reply.format(count=count, ending=ending)
        self.send_message()


class CatMessage(UpdateMessageHandler):
    reply = "🐈‍⬛"

    def __call__(self):
        self.send_message()


def main():
    print('START!!!')

    BOT = Bot(token=settings.BOT_TOKEN)
    updater = Updater(token=settings.BOT_TOKEN)

    updater.dispatcher.add_handler(CommandHandler("start", Start.as_handler))
    updater.dispatcher.add_handler(CommandHandler("info", SendInfo.as_handler))
    updater.dispatcher.add_handler(CommandHandler("kiskis", GetPhoto.as_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, PutPhoto.as_handler))
    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.regex(r'|'.join(Start.buttons)), GetPhotoAfterFeeding.as_handler
        )
    )
    updater.dispatcher.add_handler(MessageHandler(Filters.text, AnyMessage.as_handler))

    updater.start_polling()
    updater.idle()

    # while True:
    #     if not OffsetUpdateId.objects.all().exists():
    #         OffsetUpdateId.objects.create(offset=0)

    #     offset: OffsetUpdateId = OffsetUpdateId.objects.last()
    #     updates = BOT.get_updates(offset.offset)
    #     if updates:
    #         offset.offset = updates[-1].update_id + 1
    #         offset.save()

    #     logging.info('custom polling')
    #     logging.info(f'{updates=}')
    #     updated = False
    #     for update in updates:
    #         # t = UpdateHistory.objects.filter(update_id=update.update_id).all()
    #         # if t.count():
    #         #     logging.info(f'{update.update_id=} is already proccessed at {t.first().created}')
    #         #     continue

    #         logging.info(f'{offset.offset=} | {update.update_id=} is proccessing')
    #         UpdateHistory.objects.create(update_id=update.update_id)

    #         message = update.message
    #         if not message:
    #             continue

    #         context: CallbackContext = CallbackContext(updater.dispatcher)
    #         if message.photo:
    #             PutPhoto.as_handler(update, context)
    #             continue

    #         if not message.text:
    #             AnyMessage.as_handler(update, context)
    #             continue

    #         if 'start' in message.text:
    #             Start.as_handler(update, context)
    #         elif 'info' in message.text:
    #             SendInfo.as_handler(update, context)
    #         elif 'kiskis' in message.text:
    #             GetPhoto.as_handler(update, context)
    #         elif re.search(r'|'.join(Start.buttons), message.text) is not None:
    #             GetPhotoAfterFeeding.as_handler(update, context)
    #         else:
    #             AnyMessage.as_handler(update, context)

    #         updated = True

    #     sleep(2)

    #     if updated:
    #         pass
    #         # CatMessage.as_handler(update, context)

    #     sleep(3)

    # now = datetime.now()
    # for time in Start.sheldue:
    #     if time.hour == now.hour and time.min == now.min:
    #         try:
    #             Start(update, context).callback(context)
    #         except Exception as e:
    #             logging.error(e)

    # self.context.job_queue.run_daily(
    #     self.callback,
    #     context=self.chat.id,
    #     time=datetime(
    #         year=now.year,
    #         month=now.month,
    #         day=now.day,
    #         hour=now.hour,
    #         minute=now.minute,
    #         second=now.second + 5,
    #     ),
    # )


if __name__ == "__main__":
    main()
