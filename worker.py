"""

developing:
[ ] удалить одинаковые фотки не по айди, а реально сравнив фотки,
    добавить эту проверку в обработчик при каждом запросе к all
[ ] sheldue message :(
[ ] переделать все на self.message.reply_photo

[ ] multyply reply for uploaded photo


"""


from __future__ import annotations
import functools

import json
import logging
import os
import random
from datetime import datetime, timedelta, timezone
import re
from time import sleep

MSC_TZ = timezone(offset=timedelta(hours=3), name='MSC')

from typing import Callable, TypeVar

from telegram import (
    Bot,
    Chat,
    InputMediaPhoto,
    Message,
    PhotoSize,
    ReplyKeyboardMarkup,
    Update,
    User,
)
from telegram.error import BadRequest, RetryAfter
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)


import settings
from settings import logger

############################################################

BOT = None


class NoneValueError(ValueError):
    pass


_T = TypeVar('_T')


def is_not_none(obj) -> _T:
    if obj is None:
        raise NoneValueError(obj)
    return obj


class UpdateMessageHandler:
    reply: str = ''
    permissions: list[Callable[[UpdateMessageHandler], bool]] = (
        [
            lambda self: self.user.id == settings.ADMIN_CHAT_ID,
        ]
        if settings.DEBUG
        else []
    )

    def __init__(self, update: Update, context: CallbackContext) -> None:
        self.update = update
        self.context = context

        self.chat: Chat = is_not_none(update.effective_chat)
        self.message: Message = is_not_none(update.message)
        if self.message:
            self.user: User = is_not_none(self.message.from_user)

    def __call__(self):
        self.send_message()

    def reply_format(self):
        try:
            return self.reply.format()
        except KeyError as e:
            raise NotImplementedError(
                f'Ivnalid implementation for formating {self.reply=}. '
                f'{e.__class__}: {e}'
            )

    def send_message(self, **kwargs):
        kwargs['chat_id'] = kwargs.get('chat_id') or self.chat.id
        kwargs['text'] = kwargs.get('text') or self.reply_format()
        kwargs['timeout'] = kwargs.get('timeout') or 20

        try:
            self.context.bot.send_message(**kwargs)
            logger.info(f'Succcess send message {kwargs["text"]}')
        except RetryAfter as e:
            logger.warning(f'Warning {e}. Sleep {e.retry_after + 1} seconds.')
            sleep(e.retry_after + 1)
            logger.info(f'Trying send message again.')
            self.context.bot.send_message(**kwargs)
            logger.info(f'Succcess send message {kwargs["text"]}')

    @classmethod
    def as_handler(cls, update: Update, context: CallbackContext):
        try:
            handler = cls(update, context)
        except ValueError as e:
            logging.warning(f'Unexpected response from API: {e.args}')
            if update.message:
                update.message.reply_text(VerboseErrorMessage.reply)
        else:
            if all(permission(handler) for permission in cls.permissions):
                try:
                    handler()
                except Exception as e:
                    logger.exception(f'Error: unhandled exception. ')
                    if update.message:
                        update.message.reply_text(VerboseErrorMessage.reply)
            else:
                raise PermissionError

    @classmethod
    def as_callback(cls, context: CallbackContext):
        # if context.job is None:
        #     raise NoneValueError

        if context.job is None:
            raise NoneValueError(f'{context.job=}')
        if not isinstance(context.job.context, dict):
            raise TypeError(f'Invalid {type(context.job.context)}')

        try:
            update = context.job.context['update']
        except KeyError as e:
            raise ValueError(f'Invalid {context.job.context}: {e}')

        try:
            callback = cls(update, context)
        except ValueError as e:
            logging.warning(f'Unexpected response from API: {e.args}')
        else:
            if all(permission(callback) for permission in cls.permissions):
                callback()
            else:
                raise PermissionError


class Start(UpdateMessageHandler):
    reply = "мяу, {name} 🐈‍⬛ \nзагрузи сюда фотки, да побольше"
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
        # test
        datetime(
            year=2022,
            month=7,
            day=31,
            hour=19 - 3,
            minute=16,
            second=0,
        ),
    ]

    def reply_format(self):
        return self.reply.format(name=self.user.name)

    def callback(self, context):
        self.send_message(text='test callback')

    def __call__(self):

        for time in self.sheldue:
            self.context.job_queue.run_daily(
                # functools.partial(FeedMeSheldue.as_callback, update=self.update),
                FeedMeSheldue.as_callback,
                time=time,
                name=FeedMeSheldue.__name__,
                context={'update': self.update},
            )

        if settings.DEBUG:
            now = datetime.now(tz=MSC_TZ)
            time = datetime.time(now)
            for wait_sec in [0, 1, 2]:
                self.context.job_queue.run_daily(
                    type(
                        'TestSHeldue',
                        (FeedMeSheldue,),
                        {'reply': 'test sheldue reply'},
                    ).as_callback,
                    time=time,
                    name=FeedMeSheldue.__name__,
                )

            now = datetime.now()
            self.context.job_queue.run_daily(
                self.callback,
                time=datetime(
                    year=now.year,
                    month=now.month,
                    day=now.day,
                    hour=now.hour,
                    minute=now.minute,
                    second=now.second + 5,
                ),
            )

        self.send_message(
            reply_markup=(
                ReplyKeyboardMarkup(
                    [self.buttons[0:3], self.buttons[3:6], self.buttons[6:9]],
                    resize_keyboard=True,
                )
            ),
        )


class JsonFileOperator:
    file_path = 'messages_data'
    bot: Bot | None = None

    @classmethod
    def get_all(cls) -> list[Message]:
        if not cls.bot:
            raise RuntimeError('bot field should be definded')

        with open(cls.file_path, 'r') as file:
            data_str = file.read()
            if not data_str:
                logger.warning(f'Epty file "{cls.file_path}"')
                return []

            data_json: list = json.loads(data_str)
            if not isinstance(data_json, list):
                raise ValueError(f'Unexpected json file "{cls.file_path}" value')
            messages: list[Message] = [
                is_not_none(Message.de_json(single_message_json, bot=cls.bot))
                for single_message_json in data_json
            ]

        # unique constraint cheker
        if settings.DEBUG:
            photos = [next(reversed(m.photo)) for m in messages]
            photos_set: set[PhotoSize] = set(photos)
            if len(photos) != len(photos_set):
                logger.warning(
                        f'Unique constraint failed.'
                    )



        return messages

    @classmethod
    def append(cls, message: Message):
        with open(cls.file_path, 'r+') as file:

            # DELETE LAST LINE
            # Move the pointer (similar to a cursor in a text editor) to the end of the file
            file.seek(0, os.SEEK_END)

            # This code means the following code skips the very last character in the file -
            # i.e. in the case the last line is null we delete the last line
            # and the penultimate one
            pos = file.tell()

            # Read each character in the file one at a time from the penultimate
            # character going backwards, searching for a newline character
            # If we find a new line, exit the search
            while pos > 0 and file.read(1) != "]":
                pos -= 1
                file.seek(pos, os.SEEK_SET)

            # So long as we're not at the start of the file, delete all the characters ahead
            # of this position
            if pos > 0:
                file.seek(pos, os.SEEK_SET)
                file.truncate()

                # comma seperator
                file.write(',\n')
            else:
                # empty file -> new list openned seperator
                file.write('[\n')

            # append data
            file.write(message.to_json())
            file.write('\n]')  # end of list

    @classmethod
    def rewrite(cls, messages: list[Message]):
        with open(cls.file_path, 'w') as file:
            data: list[str] = []
            for msg in messages:
                j = msg.to_json()
                data.append(j)
            str_data = ',\n'.join(data)
            file.write('[\n' + str_data + '\n]')





class GetAllPhotos(UpdateMessageHandler):
    reply = 'а я такой красивый, смотри какой! только не торопись'

    def __call__(self):
        messages = JsonFileOperator.get_all()
        if not messages:
            self.reply = 'а где фотки?'
            self.send_message()
            return

        biggest_photos = [next(reversed(message.photo)) for message in messages]

        self.send_message()
        self.send_photos(biggest_photos)

    def send_photos(self, photos: list[PhotoSize]):
        per_page = 10
        pages_amount = int(len(photos) / per_page)

        start = 0
        end = 0

        for page in range(pages_amount):
            start = page * per_page
            end = start + per_page
            self.context.bot.send_media_group(
                self.chat.id, [InputMediaPhoto(media=id) for id in photos[start:end]]
            )
            logger.info(f'Send media group with {end-start} photos successfully')
            self.send_message(text=f'фотки c {start} по {end} из {len(photos)}')

        # отправим остаток
        start = end
        end = len(photos)
        self.context.bot.send_media_group(
            self.chat.id, [InputMediaPhoto(media=id) for id in photos[start:end]]
        )
        logger.info(f'Send media group with {end-start} photos successfully')
        self.send_message(text=f'фотки c {start} по {end} из {len(photos)}')


class GetPhoto(UpdateMessageHandler):
    reply = "мя"

    def __call__(self):
        messages = JsonFileOperator.get_all()
        if not messages:
            self.reply = 'а где фотки?'
            self.send_message()
            return
        message = random.choice(messages)

        biggest_photo = next(reversed(message.photo))
        self.send_message()
        self.send_photo(biggest_photo.file_id)

    def send_photo(self, photo_id):
        self.context.bot.send_photo(self.chat.id, photo_id)

class VerboseErrorMessage(UpdateMessageHandler):
    reply = 'кажется я сломался :( спроси у Миши, он починет'

class DeletePhoto(UpdateMessageHandler):
    reply_no_photo_selected = 'выбери, какой я тебе не мрррравлюсь'
    reply_succes = 'согласен, здесь я не очень, мя'

    def __call__(self):
        if self.message.reply_to_message is None:
            logger.warning(f'Delete photo failed: {self.message.reply_to_message=}')
            self.send_message(text=self.reply_no_photo_selected)
            return
        replyed_to = self.message.reply_to_message
        if not replyed_to.photo:
            logger.warning(f'Delete photo failed: {replyed_to.photo=}')
            self.send_message(text=self.reply_no_photo_selected)
            return

        messages_data = JsonFileOperator.get_all()
        filtered = list(filter(lambda m: m.photo == replyed_to.photo, messages_data))

        if not filtered:
            logger.error(f'Delete photo error: {filtered=}')
            self.send_message(text=VerboseErrorMessage.reply)
            return
        if len(filtered) > 1:
            logger.warning(f'Unique constraint failed: {filtered=}')

        messages_data.remove(filtered[0])
        JsonFileOperator.rewrite(messages_data)
        logger.info('Delete photo succesfully')
        self.send_message(text=self.reply_succes)


class FeedMeSheldue(UpdateMessageHandler):
    reply = f'я очень голодный, сейчас нашкодю!! покорми меня'

    def __call__(self):
        self.send_message()


class GetPhotoAfterFeeding(GetPhoto):
    reply = f'хрум хрум вкусненько'


class PutPhoto(UpdateMessageHandler):
    reply = f"спасибо, очень вкусно, мрррр"

    def __call__(self):
        JsonFileOperator.append(message=self.message)
        logger.info(f'Append photo to {JsonFileOperator.file_path} seccessfully. ')
        self.send_message()


class AnyMessage(UpdateMessageHandler):
    reply = "я кушал уже {count} раз{ending}, но этого не достаточно, хочу еще"

    def reply_format(self):
        return self.reply.format(count=len(JsonFileOperator.get_all()), ending='')

    def __call__(self):
        # count = MessageHistory.objects.get_all().count()
        # ending = ''
        # self.reply = self.reply.format(count=count, ending=ending)
        self.send_message()


class CatMessage(UpdateMessageHandler):
    reply = "🐈‍⬛"

    def __call__(self):
        self.send_message()


def main():
    logger.info('main method is precessing')

    bot = Bot(token=settings.BOT_TOKEN)
    JsonFileOperator.bot = bot

    updater = Updater(token=settings.BOT_TOKEN)
    updater.dispatcher.add_handler(CommandHandler("start", Start.as_handler))
    # updater.dispatcher.add_handler(CommandHandler("info", SendInfo.as_handler))
    updater.dispatcher.add_handler(CommandHandler("kiskis", GetPhoto.as_handler))
    updater.dispatcher.add_handler(CommandHandler("show", GetAllPhotos.as_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, PutPhoto.as_handler))
    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.regex(r'|'.join(Start.buttons)), GetPhotoAfterFeeding.as_handler
        )
    )
    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.regex(r'пока|bye|удалить|delete|del|Del|✖️|❌|🗑'),
            DeletePhoto.as_handler,
        )
    )

    updater.dispatcher.add_handler(MessageHandler(Filters.text, AnyMessage.as_handler))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
