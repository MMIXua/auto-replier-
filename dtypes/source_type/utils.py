
from typing import Type

from . import BaseSourceType, GmailSourceType, TelegramSourceType
from . import WhatsappSourceType


def to_source_type(string: str) -> Type[BaseSourceType] | None:
    return {
        "gmail": GmailSourceType(),
        "telegram": TelegramSourceType(),
        "whatsapp": WhatsappSourceType()
    }.get(string)
