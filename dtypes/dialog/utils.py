
from . import Dialog


def to_dialog(data: dict) -> Dialog:
    return Dialog(**data)
