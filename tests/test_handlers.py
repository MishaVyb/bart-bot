import pytest
from pyrogram.types import InputMedia, InputMediaPhoto, InputMediaVideo

from configurations import AppConfig
from content import CONTENT
from tests.conftest import ClientIntegration

pytestmark = pytest.mark.anyio


async def test_start_handler(vybornyy: ClientIntegration, config: AppConfig):
    async with vybornyy.collect(amount=1) as replyes:
        await vybornyy.client.send_message(config.botname, '/start')

    assert replyes[0].text == CONTENT.messages.start.format(username=vybornyy.tg_user.username or '')


async def test_photo_handler(vybornyy: ClientIntegration, config: AppConfig, images: list[str]):
    # [1] test single photo
    async with vybornyy.collect(amount=1) as replyes:
        await vybornyy.client.send_photo(config.botname, images[0])

    assert replyes[0].text in CONTENT.messages.receive_photo.initial  # for the first photo received

    # [2] test many photos
    async with vybornyy.collect(
        # amount=1, # TODO one reply for whole message group
    ) as replyes:
        await vybornyy.client.send_media_group(config.botname, [InputMediaPhoto(image) for image in images[1:]])

    assert replyes[0].text in CONTENT.messages.receive_photo.basic
