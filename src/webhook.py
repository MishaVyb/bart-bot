"""
Enterpoint for Yandex.Cloud function calls which used as webhook for Telegram.
"""
import json
import sys
from pathlib import Path
from typing import TypeAlias

from telegram import Update

# add application workdir.
# sys.path.append(str(Path(__file__).resolve() / 'src'))
sys.path.append(str(Path(__file__).resolve().parent))

from application import app
from configurations import CONFIG, logger

_RuntimeContext: TypeAlias = object  # NOTE: ...


async def handler(event: dict, context: _RuntimeContext):
    logger.info(f'Handle updates for {CONFIG.appname}. ')
    try:
        # NOTE
        # depending on Yandex.Functions settings, request body could be not parsed yet
        data = event['body']
        if isinstance(data, str):
            data = json.loads(data)

        await app.initialize()
        await app.process_update(Update.de_json(data=data, bot=app.bot))
    except:
        # TODO
        # special handling
        raise
    else:
        return {
            'statusCode': 200,
            'body': 'Proceeded successfully. ',
        }


# TODO
# set web hook function...
