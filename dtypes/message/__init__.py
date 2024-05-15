
from typing import Type

from dtypes.source_type import BaseSourceType, to_source_type
from dtypes.message.statuses import to_msg_status
from utils.jsonify import Jsonified

from .statuses import BaseMsgStatus


class Message(Jsonified):
    name = "message"
    id: str
    reply_to_id: str
    dialog_id: str
    sender_id: str
    source: Type[BaseSourceType]
    status: Type[BaseMsgStatus]
    text: str
    reviewed: bool
    date: int

    def __init__(
            self,
            id: str,
            dialog_id: str,
            sender_id: str,
            source: str,
            status: str,
            text: str,
            reply_to_id: str = None,
            source_link: str = None,
            subject: str = None,
            reviewer_id: str = None,
            reviewed: bool = False,
            date: int = None
    ):
        self.id = id
        self.reviewer_id = reviewer_id
        self.reviewed = reviewed
        self.reply_to_id = reply_to_id
        self.dialog_id = dialog_id
        self.sender_id = sender_id

        self.source = to_source_type(source)
        self.source.name = "source"

        self.status = to_msg_status(status)
        self.status.name = "status"

        self.text = text

        self.source_link = source_link
        self.subject = subject

        self.date = date

        self.fields = ["id", "reply_to_id", "reviewer_id", "reviewed", "dialog_id", "sender_id", "source", "source_link", "subject", "status", "date", "text"]

    def __str__(self):
        return f"Message(id={self.id})"

    def set_status(self, status: Type[BaseMsgStatus]):
        self.status = status
        self.status.name = "status"


from .utils import to_message
