from __future__ import annotations

import random

import yaml
from pydantic import BaseModel
from pydantic.validators import list_validator

from configurations import CONFIG


class Replyes(list[str]):
    def get(self, *, random_choice: bool = True):
        return random.choice(self)

    @classmethod
    def __get_validators__(cls):
        yield list_validator
        yield cls.list_tranformation

    @classmethod
    def list_tranformation(cls, v: list):
        return cls(v)


class BotContent(BaseModel):
    buttons: tuple[str, str, str, str, str, str, str, str, str]
    messages: BotMessages
    confirm_answers: list[str]
    reject_answers: list[str]

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


class SendPhotoReplyes(BaseModel):
    any: Replyes
    all: Replyes


class ReceivePhotoReplyes(BaseModel):
    initial: Replyes
    basic: Replyes


class ExceptionMessages(BaseModel):
    default: str
    repeated_photo: str
    no_photos: str

    user_not_start_bot: str
    already_added_to_famely: str


class FamelyHandlingReplyes(BaseModel):
    request_for_adding_to_famely: str


class BotMessages(BaseModel):
    start: str
    regular: Replyes
    """Replyes for any (not specific) message."""

    feedme: Replyes
    receive_food: Replyes
    send_photo: SendPhotoReplyes
    receive_photo: ReceivePhotoReplyes
    famely: FamelyHandlingReplyes
    exceptions: ExceptionMessages  # TODO move to BotContent layer


BotContent.update_forward_refs()
CONTENT = BotContent.parse_yaml(CONFIG.content_filepath)
