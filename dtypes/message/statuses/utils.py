
from typing import Type

from . import BaseMsgStatus, WaitingForSendMsgStatus, ReadMsgStatus, ReceivedMsgStatus
from . import SentMsgStatus, BlankReplyMsgStatus, ErrorSendingMsgStatus, ReviewedMsgStatus
from . import WaitingForReviewStatus, ErrorReviewingMsgStatus


def to_msg_status(string: str) -> Type[BaseMsgStatus]:
    statuses = [
        WaitingForSendMsgStatus, ReadMsgStatus, ReceivedMsgStatus,
        SentMsgStatus, BlankReplyMsgStatus, ErrorSendingMsgStatus,
        ReviewedMsgStatus, WaitingForReviewStatus, ErrorReviewingMsgStatus
    ]
    return {
        status.string: status() for status in statuses
    }.get(string)
