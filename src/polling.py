"""
Enterpoint for handling Telegram bot updates by long polling.
"""
from application import app
from configurations import CONFIG, logger


def main() -> None:
    logger.info(f'Start {CONFIG.appname} polling. Listening for updates. ')
    app.run_polling()


if __name__ == "__main__":
    main()
