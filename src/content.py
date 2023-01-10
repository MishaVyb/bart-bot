from __future__ import annotations

import yaml
from pydantic import BaseModel

from configurations import CONFIG


class BotContent(BaseModel):
    buttons: tuple[str, str, str, str, str, str, str, str, str]
    messages: BotMessages

    @property
    def keyboard(self):
        return [self.buttons[0:3], self.buttons[3:6], self.buttons[6:9]]

    @classmethod
    def parse_yaml(cls, filepath: str):
        with open(filepath, 'r') as file:
            content = yaml.safe_load(file)

        return cls.parse_obj(content)

    class Config:
        ...
        # TODO frozen


class _send_photo(BaseModel):
    any: str
    all: str


class _receive_photo(BaseModel):
    initial: list[str]
    basic: list[str]


class _exceptions(BaseModel):
    default: str
    repeated_photo: str
    no_photos: str


class BotMessages(BaseModel):
    start: str
    regular: list[str]
    feedme: list[str]
    receive_food: list[str]
    send_photo: _send_photo
    receive_photo: _receive_photo
    exceptions: _exceptions  # TODO move to BotContent layer


BotContent.update_forward_refs()
CONTENT = BotContent.parse_yaml(CONFIG.content_filepath)
