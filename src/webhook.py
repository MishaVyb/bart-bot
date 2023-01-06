import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

from telegram import Update

# add application workdir
# sys.path.append(str(Path(__file__).resolve() / 'src'))
sys.path.append(str(Path(__file__).resolve().parent))

from application import app

if TYPE_CHECKING:
    _RuntimeContext: TypeAlias = object  # NOTE: ...


async def handler(event: dict, context: _RuntimeContext):
    try:
        # NOTE
        # raw `request body` already parsed to json dict by Yandex server internally
        data = event['body']

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
