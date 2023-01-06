"""
Enterpoint for handling Telegram bot updates by long polling.
"""

import sys
from pathlib import Path

# add application workdir
sys.path.append(str(Path(__file__).resolve().parent / 'src'))

from application import app


def main() -> None:
    app.run_polling()


if __name__ == "__main__":
    main()
