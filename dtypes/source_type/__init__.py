
from utils.jsonify import JsonifiedProperty


class BaseSourceType(JsonifiedProperty):
    name = "source_type"
    string = "base"
    field = "string"

    def __init__(self):
        self.string = self.string

    def __str__(self):
        return self.string


from .source_type import GmailSourceType, TelegramSourceType
from .source_type import WhatsappSourceType
from .utils import to_source_type
