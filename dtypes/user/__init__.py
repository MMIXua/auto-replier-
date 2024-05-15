
from typing import Type

from dtypes.source_type import BaseSourceType, to_source_type

from utils.jsonify import Jsonified


class BaseUser(Jsonified):
    name: str = "user"
    type: str = "base_user"
    id: str
    link: str
    source: Type[BaseSourceType]
    firstname: str
    phone: str
    first_message: int
    last_message: int

    def __init__(self, id: str, link: str, source: str, firstname: str = None, phone: str = None, first_message: int = None, last_message: int = None):
        self.name = self.name
        self.type = self.type
        self.id = id
        self.link = link
        self.firstname = firstname
        self.phone = phone
        self.first_message = first_message
        self.last_message = last_message

        self.source = to_source_type(source)
        self.source.name = "source"

        self.fields = ["id", "type", "link", "source", "firstname", "phone", "first_message", "last_message"]

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id})"


from .user import Client, Bot, Reviwer
from .utils import to_user_type, to_user
