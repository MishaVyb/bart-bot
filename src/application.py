from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

import handlers
from configurations import CONFIG
from content import CONTENT
from persistences import YandexDiskPicklePersistence

app = (
    Application.builder()
    .token(CONFIG.bot_token.get_secret_value())
    .persistence(
        YandexDiskPicklePersistence(filepath=CONFIG.data_filepath),
        # PicklePersistence(filepath=CONFIG.data_filepath),
    )
    .build()
)


app.add_handler(CommandHandler('start', handlers.start))
app.add_handler(CommandHandler('admin_loaddata', handlers.admin_loaddata))
app.add_handler(CommandHandler('admin_flushdata', handlers.admin_loaddata))
app.add_handler(
    MessageHandler(filters.Regex(r'|'.join(CONTENT.buttons)), handlers.receive_food)
)
app.add_handler(MessageHandler(filters.PHOTO, handlers.receive_photo))
app.add_handler(MessageHandler(filters.VIDEO, handlers.receive_photo))
app.add_handler(MessageHandler(filters.TEXT, handlers.any_text))
