
from . import BaseSourceType


class GmailSourceType(BaseSourceType):
    string = "gmail"


class TelegramSourceType(BaseSourceType):
    string = "telegram"


class WhatsappSourceType(BaseSourceType):
    string = "whatsapp"
