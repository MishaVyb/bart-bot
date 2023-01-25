"""
Enterpoint for Yandex.Cloud function calls which used as webhook for Telegram.
"""
import json
import sys
from pathlib import Path
from typing import TypeAlias

from telegram import Update

sys.path.append(str(Path(__file__).resolve().parent))

from application import app
from configurations import CONFIG, logger

_RuntimeContext: TypeAlias = object  # special yandex.cloud functions object


async def gateway(event: dict, context: _RuntimeContext):

    # NOTE
    # depending on Yandex.Functions settings, request body could be not parsed yet
    data = event['body']
    if isinstance(data, str):
        data = json.loads(data)

    try:
        logger.info(f'Handle update for {CONFIG.botname}. Start app. ')
        if not app.running:
            await app.initialize()
            await app.start()
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
    finally:
        logger.info('Stop application. ')
        await app.stop()
        await app.shutdown()


# TODO
# set web hook function...
