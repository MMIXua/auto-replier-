
class ListenerOutput:
    def __init__(
        self,
        id: str,
        link: str,
        source_link: str,
        phone: str,
        firstname: str,
        message_id: str,
        text: str,
        subject: str
    ):
        self.id = id
        self.link = link
        self.source_link = source_link
        self.phone = phone
        self.firstname = firstname
        self.message_id = message_id
        self.text = text
        self.subject = subject

    def to_dict(self):
        return {
            "id": self.id,
            "link": self.link,
            "source_link": self.source_link,
            "phone": self.phone,
            "firstname": self.firstname,
            "message_id": self.message_id,
            "text": self.text,
            "subject": self.subject
        }
