from __future__ import annotations


import json
import logging
import os
import random
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Callable, ClassVar, TypeVar

import yadisk
from telegram import (Bot, Chat, InputMediaPhoto, Message, PhotoSize,
                      ReplyKeyboardMarkup, Update, User)
from telegram.error import RetryAfter
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)

import settings
from settings import logger

MSC_TZ = timezone(offset=timedelta(hours=3), name='MSC')
BOT = None
_T = TypeVar('_T')


class NoneValueError(ValueError):
    pass


def is_not_none(obj: _T | None) -> _T:
    """
    Shortcut to control types stricly.
    """
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
    reply = "??????, {name} ?????????? \n?????????????? ???????? ??????????, ???? ????????????????"
    buttons = ['????', '????', '????', '????', '????', '????', '????', '??????', '????']
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

    def reply_format(self):
        return self.reply.format(name=self.user.name)

    def callback(self, context):
        self.send_message(text='test callback')

    def __call__(self):

        for time in self.sheldue:
            self.context.job_queue.run_daily(
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
            try:
                self.context.job_queue.run_daily(
                    self.callback,
                    time=datetime(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        hour=now.hour,
                        minute=now.minute,
                        second=now.second + wait_sec,
                    ),
                )
            except Exception as e:
                logger.warning(e)

        self.send_message(
            reply_markup=(
                ReplyKeyboardMarkup(
                    [self.buttons[0:3], self.buttons[3:6], self.buttons[6:9]],
                    resize_keyboard=True,
                )
            ),
        )


class ConstraintError(Exception):
    pass


class JsonFileOperator:
    bot: Bot | None = None
    yadisk: YaDisk | None = None

    _remote_file_folder = '/bart-bot-2.0/'
    _remote_file_name = 'bart_bot_yandex_disk_storage_messages_data'
    remote_file_path = _remote_file_folder + _remote_file_name

    _local_file_folder = ''
    _local_file_name = 'local_messages_data'
    local_file_path = _local_file_folder + _local_file_name

    @classmethod
    def get_all(cls) -> list[Message]:
        if not cls.bot or not cls.yadisk:
            raise RuntimeError('bot and yadisk fields should be definded')

        try:
            cls.yadisk.download(cls.remote_file_path, cls.local_file_path)
        except FileNotFoundError:
            # create file if it does not exixt
            open(cls.local_file_path, 'w+')
            cls.yadisk.download(cls.remote_file_path, cls.local_file_path)
        except yadisk.exceptions.PathNotFoundError:
            logger.warning(
                'Remote data not phoun. '
                'Check deleted files at remoute server, data cold be there. '
                'Anyway, created new data file with no data and contunue processing. '
            )
            with open(cls.local_file_path, "w+") as f:
                f.write('')
                cls.yadisk.upload(f, cls.remote_file_path)

        with open(cls.local_file_path, 'r') as file:
            data_str = file.read()
            if not data_str:
                logger.warning(f'No data')
                return []

            try:
                data_json: list = json.loads(data_str)
            except json.decoder.JSONDecodeError as e:
                raise ValueError(f'Unexpected json file value: {e}')

            if not isinstance(data_json, list):
                raise ValueError(f'Unexpected json file value: {type(data_json)}')
            messages: list[Message] = [
                is_not_none(Message.de_json(single_message_json, bot=cls.bot))
                for single_message_json in data_json
            ]

        # ?????????????? ?? ???????????????????? ??????????
        # os.remove(cls.local_file_path)

        # unique constraint cheker
        photos = [next(reversed(m.photo)) for m in messages]
        photos_set: set[PhotoSize] = set(photos)
        if len(photos) != len(photos_set):
            logger.warning(f'Unique constraint failed.')
            return cls.remove_not_uniq(messages)

        return messages

    @classmethod
    def remove_not_uniq(cls, messsages: list[Message]) -> list[Message]:
        logger.info('Prccessing removing repeted photos.')
        for i, msg in enumerate(messsages):
            # repeated_index = messsages.index(msg, i+1)
            filtered = filter(
                lambda m: next(reversed(m.photo)) == next(reversed(msg.photo)),
                messsages,
            )
            next(filtered)  # skip first el
            for repeated_messages in filtered:
                messsages.remove(repeated_messages)
                logger.info(f'Repeated photo #{i} removed.')

        cls.rewrite(messsages)
        return messsages

    @classmethod
    def append(cls, message: Message):
        if not cls.bot or not cls.yadisk:
            raise RuntimeError('bot and yadisk fields should be definded')

        # unique constraint cheker
        if list(
            filter(
                lambda m: next(reversed(m.photo)) == next(reversed(message.photo)),
                cls.get_all(),
            )
        ):
            raise ConstraintError('Invalid photo to append: unique constraint faild')

        try:
            # ?????????????????? ???????? ???? ?????????????????? ????????
            cls.yadisk.download(cls.remote_file_path, cls.local_file_path)
        except FileNotFoundError:
            # create file if it does not exixt
            open(cls.local_file_path, 'w+')
            cls.yadisk.download(cls.remote_file_path, cls.local_file_path)


        with open(cls.local_file_path, 'r+') as file:
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

        # ?????????????????? ???? ???????????? ???????? ?????????? ????????
        with open(cls.local_file_path, "rb") as f:
            try:
                cls.yadisk.upload(f, cls.remote_file_path)
            except yadisk.exceptions.PathExistsError:
                # ?????????????? ?? ???????????? ??????????
                logger.warning('Start replacing remote storage file: delete it first.')
                cls.yadisk.remove(cls.remote_file_path, permanently=False)
                cls.yadisk.upload(f, cls.remote_file_path)
                logger.info('Remote storage file replaced succesfully')

        # ?????????????? ?? ???????????????????? ??????????
        # os.remove(cls.local_file_path)
        logger.info('Append photo to remote storage seccessfully')

    @classmethod
    def rewrite(cls, messages: list[Message]):
        if not cls.bot or not cls.yadisk:
            raise RuntimeError('bot and yadisk fields should be definded')

        try:
            # ?????????????????? ???????? ???? ?????????????????? ????????
            cls.yadisk.download(cls.remote_file_path, cls.local_file_path)
        except FileNotFoundError:
            # create file if it does not exixt
            open(cls.local_file_path, 'w+')
            cls.yadisk.download(cls.remote_file_path, cls.local_file_path)

        with open(cls.local_file_path, 'w') as file:
            if not messages:
                # epty messages list for del all porpuse
                # file becomes epty in that way
                file.write('')
            else:
                data: list[str] = []
                for msg in messages:
                    j = msg.to_json()
                    data.append(j)
                str_data = ',\n'.join(data)
                file.write('[\n' + str_data + '\n]')

        # ?????????????????? ???? ???????????? ???????? ?????????? ????????
        with open(cls.local_file_path, "rb") as f:
            try:
                cls.yadisk.upload(f, cls.remote_file_path)
            except yadisk.exceptions.PathExistsError:
                # ?????????????? ?? ???????????? ??????????
                logger.warning('Start replacing remote storage file: delete it first.')
                cls.yadisk.remove(cls.remote_file_path, permanently=False)
                cls.yadisk.upload(f, cls.remote_file_path)
                logger.info('Remote storage file replaced succesfully')

        # ?????????????? ?? ???????????????????? ??????????
        # os.remove(cls.local_file_path)
        logger.info('Append photo to remote storage seccessfully')


class GetAllPhotos(UpdateMessageHandler):
    reply = '?? ?? ?????????? ????????????????, ???????????? ??????????! ???????????? ???? ????????????????'

    def __call__(self):
        messages = JsonFileOperator.get_all()
        if not messages:
            self.reply = '?? ?????? ???????????'
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

            # +1 becaues human verbose count representation
            self.send_message(text=f'?????????? c {start + 1} ???? {end} ???? {len(photos)}')

        # ???????????????? ?????????????? ???????? ???? ????????
        start = end
        end = len(photos)
        if start < end:
            self.context.bot.send_media_group(
                self.chat.id, [InputMediaPhoto(media=id) for id in photos[start:end]]
            )
            logger.info(f'Send media group with {end-start} photos successfully')
            self.send_message(text=f'?????????? c {start} ???? {end} ???? {len(photos)}')


class GetPhoto(UpdateMessageHandler):
    reply = "????"

    def __call__(self):
        messages = JsonFileOperator.get_all()
        if not messages:
            self.reply = '?? ?????? ???????????'
            self.send_message()
            return
        message = random.choice(messages)

        biggest_photo = next(reversed(message.photo))
        self.send_message()
        self.send_photo(biggest_photo.file_id)

    def send_photo(self, photo_id):
        self.context.bot.send_photo(self.chat.id, photo_id)


class VerboseErrorMessage(UpdateMessageHandler):
    reply = '?????????????? ?? ???????????????? :( ???????????? ?? ????????, ???? ??????????????'


class DeletePhoto(UpdateMessageHandler):
    reply_no_photo_selected = '????????????, ?????????? ?? ???????? ???? ??????????????????????'
    reply_succes = '????????????????, ?????????? ?? ???? ??????????, ????'

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


class DeleteAllPhotos(UpdateMessageHandler):
    reply = '???????? ???????????? ??????...'

    def __call__(self):
        JsonFileOperator.rewrite([])
        logger.info('Delete all photos succesfully')
        self.send_message()


class FeedMeSheldue(UpdateMessageHandler):
    reply = f'?? ?????????? ????????????????, ???????????? ??????????????!! ?????????????? ????????'

    def __call__(self):
        self.send_message()


class GetPhotoAfterFeeding(GetPhoto):
    reply = f'???????? ???????? ????????????????????'


class PutPhoto(UpdateMessageHandler):
    replys = [
        '??????????',
        'o?? ?????????? ??',
        '?????????????? ??????????????',
        '?????????????? ???? ??????????',
        '????',
        '?????? ?????? ?? ??????????????',
        '???? ???????????? ??????????',
        '?? ?????? ???? ??',
    ]
    reply_repeated_photo = '???? ???? ???????????????????? ????'
    prev_media_group_id: ClassVar[int | None] = None

    def __call__(self):
        try:
            JsonFileOperator.append(message=self.message)
        except ConstraintError:
            logger.info('Ignored repeated photo')
            self.send_message(text=self.reply_repeated_photo)
            return

        prev = self.prev_media_group_id
        current = self.message.media_group_id
        if prev and prev == current:
            return
        PutPhoto.prev_media_group_id = current
        self.send_message(text=random.choice(self.replys))


class CountMessage(UpdateMessageHandler):
    replys = [
        '?? ?????????????????? ?????? {count} ??????{ending}',
        '???? ?????????? ???? ????????????????????, ???????????? ??????',
    ]
    pause_duration = 0.5
    reply_no_photos = '???????? ????????..'

    def reply_format(self) -> list[str]:
        count = len(JsonFileOperator.get_all())
        if count:
            return [self.replys[0].format(count=count, ending=''), self.replys[1]]
        else:
            return [self.reply_no_photos]

    def __call__(self):
        for msg in self.reply_format():
            self.send_message(text=msg)
            sleep(self.pause_duration)


class CatMessage(UpdateMessageHandler):
    replys = [
        '??????????',
        '??????????????',
        '???? ???? ????',
        '????????????????',
        '??????????',
        '????',
        '????',
        '????????',
        '...',
        '?????????? ??????????',
        '???????? ????????',
        '?? ?????? ???????!',
    ]

    def __call__(self):
        self.send_message(text=random.choice(self.replys))


from yadisk import YaDisk


def main():
    logger.info('main method is precessing')
    if not all([settings.BOT_TOKEN, settings.ADMIN_CHAT_ID, settings.YADISK_TOKEN]):
        raise RuntimeError('Invalid environment variables')

    bot = Bot(token=settings.BOT_TOKEN)
    JsonFileOperator.bot = bot
    JsonFileOperator.yadisk = YaDisk(token=settings.YADISK_TOKEN)

    updater = Updater(token=settings.BOT_TOKEN)
    updater.dispatcher.add_handler(CommandHandler("start", Start.as_handler))
    # updater.dispatcher.add_handler(CommandHandler("info", SendInfo.as_handler))
    # updater.dispatcher.add_handler(CommandHandler("kiskis", GetPhoto.as_handler))
    updater.dispatcher.add_handler(CommandHandler("show", GetAllPhotos.as_handler))
    updater.dispatcher.add_handler(CommandHandler("count", CountMessage.as_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, PutPhoto.as_handler))
    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.regex(r'|'.join(Start.buttons)), GetPhotoAfterFeeding.as_handler
        )
    )
    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.regex(r'del all password: vbrn|Del all password: vbrn'),
            DeleteAllPhotos.as_handler,
        )
    )
    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.regex(r'????????|bye|??????????????|delete|del|Del|??????|???|????'),
            DeletePhoto.as_handler,
        )
    )

    updater.dispatcher.add_handler(MessageHandler(Filters.text, CatMessage.as_handler))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
