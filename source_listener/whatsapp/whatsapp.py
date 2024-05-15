
from typing import Type

from dtypes.message import Message
from dtypes.user import BaseUser
from dtypes.source_type import WhatsappSourceType
from dtypes.dialog import Dialog
from source_listener import BaseSourceListener, ListenerOutput

from bs4 import BeautifulSoup

from heyoo import WhatsApp

from config import WHATSAPP_TOKEN, WHATSAPP_PHONE
from config import DATABASE_CHECK_DELAY, API

from utils import string_to_uuid

from .wphook import run_app


CONN_API = API["conn"]["entry"]
PUB_API = API["pub"]["entry"]


class WhatsappSourceListener(BaseSourceListener):
    source_type = WhatsappSourceType()
    outcoming_delay = DATABASE_CHECK_DELAY

    async def callback(self, data):

        for entry in data["entry"]:
            for change in entry["changes"]:
                value = change["value"]

                contacts = value["contacts"]
                if len(contacts) == 0:
                    continue
                client = contacts[0]

                messages = value["messages"]
                if len(messages) == 0:
                    continue
                message = messages[0]

                await self.save_message(ListenerOutput(
                    message_id=str(message["id"]),
                    text=message["text"]["body"],
                    link=f"https://wa.me/{client['wa_id']}",
                    firstname=client["profile"]["name"],
                    phone=client['wa_id'],
                    id=string_to_uuid(client["wa_id"]),
                    subject=None,
                    source_link=None
                ))

    async def _connect(self):
        self.client = WhatsApp(WHATSAPP_TOKEN, phone_number_id=WHATSAPP_PHONE)

    async def listen_incoming_messages(self):
        await run_app(self.callback)

    async def _send_message(self, reciepient: Type[BaseUser], message: Message, ask_message: Message, dialog: Dialog):
        soup = BeautifulSoup(message.text)
        self.client.send_message(
            message=soup.get_text(),
            recipient_id=reciepient.phone
        )
