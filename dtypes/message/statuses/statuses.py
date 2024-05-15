
from . import BaseMsgStatus


class ReceivedMsgStatus(BaseMsgStatus):
    string = "received"


class BlankReplyMsgStatus(BaseMsgStatus):
    string = "blank_reply"


class WaitingForSendMsgStatus(BaseMsgStatus):
    string = "waiting_for_send"


class ReadMsgStatus(BaseMsgStatus):
    string = "read"


class SentMsgStatus(BaseMsgStatus):
    string = "sent"


class ErrorSendingMsgStatus(BaseMsgStatus):
    string = "error_sending"


class WaitingForReviewStatus(BaseMsgStatus):
    string = "waiting_for_review"


class ReviewedMsgStatus(BaseMsgStatus):
    string = "reviewed"


class ErrorReviewingMsgStatus(BaseMsgStatus):
    string = "error_reviewing"


class ErrorGeneratingAnswer(BaseMsgStatus):
    string = "error_generating"
