from application.middlewares import session_context
from configurations import CONFIG, logger
from content import CONTENT
from service import AppService


async def send_feed_me_message_task():
    from .application import app

    logger.info('Running send_feed_me_message_task. ')

    async with session_context() as session:

        for chat_id in CONFIG.send_feed_me_chat_ids:
            user = await AppService(session, None, None).get_user(chat_id)
            service = AppService(session, user, None)

            logger.info('Sending message to: %s', chat_id)

            photo = await service.get_media_id()
            await app.bot.send_photo(chat_id, photo, CONTENT.messages.feedme.get())
