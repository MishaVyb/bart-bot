"""
Enterpoint for handling Telegram bot updates by long polling.
"""

import sys
from pathlib import Path

# add application workdir
sys.path.append(str(Path(__file__).resolve().parent / 'src'))

from application import app
from configurations import CONFIG, logger


def main() -> None:
    logger.info(f'Start {CONFIG.app_name} polling. Listening for updates. ')
    app.run_polling()


if __name__ == "__main__":
    main()
