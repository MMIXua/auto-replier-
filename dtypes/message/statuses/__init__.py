
from utils.jsonify import JsonifiedProperty


class BaseMsgStatus(JsonifiedProperty):
    name = "msg_status"
    string = "base"
    field = "string"

    def __init__(self):
        self.string = self.string

    def __str__(self):
        return self.string


from .statuses import WaitingForSendMsgStatus, ReadMsgStatus, ReceivedMsgStatus
from .statuses import BlankReplyMsgStatus, SentMsgStatus, ErrorSendingMsgStatus
from .statuses import WaitingForReviewStatus, ReviewedMsgStatus, ErrorReviewingMsgStatus
from .statuses import ErrorGeneratingAnswer
from .utils import to_msg_status
