
from typing import Type

from . import BaseSourceListener, GmailSourceListener, TelegramSourceListener, WhatsappSourceListener


def to_source_listener_type(string: str) -> Type[BaseSourceListener]:
    return {
        "gmail": GmailSourceListener,
        "telegram": TelegramSourceListener,
        "whatsapp": WhatsappSourceListener
    }.get(string)
