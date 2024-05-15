
from . import Message


def to_message(data: dict) -> Message:
    return Message(**data)
