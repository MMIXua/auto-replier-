
from typing import Type

from . import BaseUser, Client, Bot, Reviwer


def to_user_type(string: str) -> Type[BaseUser]:
    return {
        "client": Client,
        "bot": Bot,
        "reviewer": Reviwer
    }.get(string)


def to_user(data: dict) -> Type[BaseUser]:
    user_type = data.pop("type")
    return to_user_type(user_type)(**data)
