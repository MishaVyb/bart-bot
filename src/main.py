import json
import logging
import sys
from pathlib import Path

from requests import Response
from telegram import __version__ as TG_VER

sys.path.append(str(Path(__file__).resolve().parent))

from configurations import CONFIG

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, 'alpha', 1):
    raise RuntimeError(
        f'This example is not compatible with your current PTB version {TG_VER}. To view the '
        f'{TG_VER} version of this example, '
        f'visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html'
    )

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)

application = Application.builder().token(CONFIG.bot_token).updater(None).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a message with instructions on how to use this bot."""
    text = 'Hellow World!'
    await update.message.reply_text(text=text)


# register handlers
application.add_handler(CommandHandler('start', start))

# DO IT BY HANDS
# Pass webhook settings to telegram
# await application.bot.set_webhook(url=f'{url}/telegram')

# INTERPOINT FOR WEBHOOK
async def webhook(event, context) -> Response:
    """Handle incoming Telegram updates by putting them into the `update_queue`"""
    logger.info(f'{event=}. {type(event)}')
    logger.info(f'{context=}. {type(context)}')

    update = Update.de_json(data=json.loads(event.body), bot=application.bot)
    await application.process_update(update)
    return {
        'statusCode': 200,
        'body': 'Proceeded successfully. ',
    }
