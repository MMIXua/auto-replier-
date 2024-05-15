
from typing import Type

from dtypes.source_type import BaseSourceType, to_source_type
from utils.jsonify import Jsonified


class Dialog(Jsonified):
    name = "dialog"
    id: str
    participants: list[str]
    source: Type[BaseSourceType]
    gpt_face: dict
    subjects: list

    def __init__(self, id: str, source: str, participants: list[str], gpt_face: dict | None = None):
        self.id = id

        self.source = to_source_type(source)
        self.source.name = "source"

        self.participants = participants

        self.gpt_face = gpt_face

        self.fields = ["id", "source", "participants", "gpt_face"]


from .utils import to_dialog
