from anyio import sleep
import imagehash
import pytest
from PIL import Image
from pyrogram.types import InputMediaPhoto

from configurations import AppConfig
from content import CONTENT
from tests.conftest import TestConfig
from tests.tools.integration import ClientIntegration

pytestmark = pytest.mark.anyio


async def test_start_handler(vybornyy: ClientIntegration, config: AppConfig):
    async with vybornyy.collect(amount=1) as replyes:
        await vybornyy.client.send_message(config.botname, '/start')

    assert replyes[0].text == CONTENT.messages.start.format(username=(await vybornyy.client.get_me()).username)


async def test_photo_handler(vybornyy: ClientIntegration, config: AppConfig, images: list[str]):
    # [1] check initial reply
    async with vybornyy.collect(amount=1) as replyes:
        await vybornyy.client.send_photo(config.botname, images[0])

    assert replyes[0].text in CONTENT.messages.receive_photo.initial

    # [2] check basic reply
    async with vybornyy.collect(amount=1) as replyes:
        await vybornyy.client.send_photo(config.botname, images[0])

    assert replyes[0].text in CONTENT.messages.receive_photo.basic

    # [3] check group reply
    # strict_mode -- check that bot reply only ONCE for whoole message group
    async with vybornyy.collect(amount=1, strict_mode=True) as replyes:
        await vybornyy.client.send_media_group(config.botname, [InputMediaPhoto(image) for image in images])

    assert replyes[0].text in CONTENT.messages.receive_photo.group


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
    stored_file_id = (await vybornyy.user).history[0].media_id

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


async def test_all_handler(vybornyy: ClientIntegration, config: AppConfig):
    async with vybornyy.collect(amount=1) as replyes:
        await vybornyy.client.send_message(config.botname, 'some other message')

    assert replyes[0].text in CONTENT.messages.regular


@pytest.mark.xfail
async def test_family(vybornyy: ClientIntegration, herzog: ClientIntegration, config: TestConfig, images: list[str]):
    """
    Test case:
    - Vybornyy request Herzog's storage.
    - Herzog approve.
    - Vybornyy added.
    """
    if not config.strict_mode:
        pytest.skip('strict_mode test only: username is necessary for this test case.')

    await herzog.client.send_message(vybornyy.credits.username, 'Hello, Vybornyy! ')
    message_for_forwarding = await anext(vybornyy.client.get_chat_history(herzog.credits.username))

    async with herzog.collect(amount=1, strict_mode=False):
        await herzog.client.send_message(config.botname, '/start')

    # vybornyy subscribe herzog
    async with herzog.collect(amount=2, strict_mode=False):
        async with vybornyy.collect(amount=1, strict_mode=False):
            await vybornyy.client.forward_messages(config.botname, herzog.credits.username, message_for_forwarding.id)
            await sleep(1)
            assert (await vybornyy.user).storage_request == (await herzog.user).storage

            await herzog.client.send_message(config.botname, 'yes')

    # check replyes
    assert herzog.replyes[0].text == CONTENT.messages.family.request.format(username=vybornyy.credits.username)
    assert herzog.replyes[1].text == CONTENT.messages.family.confirm
    assert vybornyy.replyes[0].text == CONTENT.messages.family.confirm

    # check shared storage
    assert (await herzog.user).storage.id == (await herzog.user).id
    assert (await vybornyy.user).storage.id == (await herzog.user).id

    assert (await vybornyy.user).storage_request == None
