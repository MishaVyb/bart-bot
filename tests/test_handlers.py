import imagehash
import pytest
from PIL import Image
from pyrogram.types import InputMediaPhoto

from configurations import AppConfig
from content import CONTENT
from tests.integration.client import ClientIntegration

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


async def test_emoji_food_handler(vybornyy: ClientIntegration, config: AppConfig, images: list[str]):
    # arrange: add 1 photo to user storage
    posted_image = images[0]
    async with vybornyy.collect():
        await vybornyy.client.send_photo(config.botname, posted_image)

    # act: send message with food
    async with vybornyy.collect(amount=2) as replyes:
        await vybornyy.client.send_message(config.botname, '🍣')

    # assertions:
    eating_message, photo_message = replyes
    assert eating_message.text in CONTENT.messages.receive_food

    received_file_id = photo_message.photo.file_id
    stored_file_id = (await vybornyy.db_user).history[0].media_id

    # NOTE:
    # Telegram has different ids for User client and Bot client
    # And it cannot be downloaded back, as user client does not know about Bot's file_id
    with pytest.raises((AssertionError, ValueError)):
        assert received_file_id == stored_file_id
    with pytest.raises(ValueError, match=r'Unknown thumbnail_source 120 of file_id .*'):
        assert await vybornyy.client.download_media(stored_file_id, in_memory=True)

    # Therefore we ensure that photo received equals to image loaded before by hash comparision
    received_file = await vybornyy.client.download_media(received_file_id, in_memory=True)
    assert imagehash.average_hash(Image.open(received_file)) == imagehash.average_hash(Image.open(posted_image))

    # query = select(MessageModel).filter(
    #     MessageModel.user_id==(await vybornyy.db_user).storage,
    #     MessageModel.media_id==received_file_id
    # )
    # result = await session.execute(query)

    # assert result.scalar_one_or_none()
    # assert replyes[1].caption in CONTENT.messages.send_photo.any
