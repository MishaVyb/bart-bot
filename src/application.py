from telegram.ext import Application, CommandHandler

from configurations import CONFIG
from handlers import start

app = (
    Application.builder().token(CONFIG.bot_token)
    #    .updater(None)
    .build()
)

app.add_handler(CommandHandler('start', start))
