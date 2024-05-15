
import aiohttp
import asyncio
from typing import Type

import telethon
from telethon import TelegramClient as TClient

from utils import clear

from dtypes.message import Message
from dtypes.message.statuses import WaitingForReviewStatus
from dtypes.user import BaseUser
from dtypes.source_type import TelegramSourceType
from dtypes.dialog import Dialog
from . import BaseSourceListener, ListenerOutput

from config import TELEGRAM_SESSION_PATH, DATABASE_CHECK_DELAY
from config import IS_DEBUG, TELEGRAM_REVIEW
from config import API


CONN_API = API["conn"]["entry"]
PUB_API = API["pub"]["entry"]


class TelegramSourceListener(BaseSourceListener):
    source_type = TelegramSourceType()
    outcoming_delay = DATABASE_CHECK_DELAY

    async def callback(self, event: telethon.events.NewMessage.Event):
        message = event.message

        if not isinstance(message.peer_id, telethon.types.PeerUser):
            return self.log.warning(f"Got message from not private chat -> {message.peer_id}")

        if not message.text:
            return self.log.warning(f"Got blank message -> {message}")

        user_entity = await event.get_sender()

        if message.reply_to_msg_id:
            http = aiohttp.ClientSession(loop=asyncio.get_running_loop())

            async with http.get(f"{CONN_API}/config", json={"id": "main"}) as response:
                config_response = await response.json()

            reviewers = list(map(lambda x: x["id"], config_response["data"]["reviewers"]))

            if str(message.peer_id.user_id) in reviewers:
                review_message = await self.client.get_messages(message.peer_id.user_id, ids=message.reply_to_msg_id)
                review_parts = review_message.text.split("\n")

                recipient_id = review_parts[2].split(": ")[-1]
                ask_message_id = review_parts[3].split(": ")[-1]
                bot_message_id = review_parts[4].split(": ")[-1]

                message = Message(**{
                    "id": '_'.join((ask_message_id, "review", str(message.peer_id.user_id))),
                    "reply_to_id": bot_message_id,
                    "dialog_id": recipient_id,
                    "sender_id": str(message.peer_id.user_id),
                    "source": str(self.source_type),
                    "status": str(WaitingForReviewStatus()),
                    "text": message.text
                })

                message_data = message.to_dict()

                self.log.debug(f"Trying to add review message -> {message_data}")
                async with http.post(f"{CONN_API}/message", json=clear(message_data)) as response:
                    message_response = await response.json()

                self.log.info(f"Got response from adding review message -> {message_response}")
                await http.close()

                return None

        return await self.save_message(ListenerOutput(
            message_id=str(message.id),
            text=message.text,
            link=f"https://t.me/{user_entity.username}" if user_entity.username else user_entity.access_hash,
            firstname=user_entity.first_name,
            phone=user_entity.phone,
            id=str(message.peer_id.user_id),
            subject=None,
            source_link=None
        ))

    async def _connect(self):
        self.client = TClient(TELEGRAM_SESSION_PATH, 1, "1")
        self.client.parse_mode = "html"
        await self.client.connect()

        if not await self.client.is_user_authorized():
            self.log.critical(f"Cant log in to session -> {TELEGRAM_SESSION_PATH}")
            exit()

        await self.client.start()
        self.log.debug("Authed account")

        self.client.add_event_handler(self.callback, telethon.events.NewMessage())

    async def listen_incoming_messages(self):
        await self.client.run_until_disconnected()

    async def _send_review_message(self, reciepient: Type[BaseUser], client: Type[BaseUser], message: Message, ask_message: Message, dialog: Dialog):
        bot_message_id = '_'.join((message.reply_to_id, "reply"))

        for template in TELEGRAM_REVIEW:
            string = template.format(
                **client.to_dict(),
                client_message_id=ask_message.id,
                bot_message_id=bot_message_id,
                source_link=ask_message.source_link if ask_message.source_link else "UNDETERMINATED",
                subject=ask_message.subject,
                text=ask_message.text,
                gpt_text=message.text,
                send_link=f'{PUB_API}/send/{bot_message_id}'
            )

            await self.client.send_message(int(reciepient.id), message=string)

    async def _send_message(self, reciepient: Type[BaseUser], message: Message, ask_message: Message, dialog: Dialog):
        await self.client.send_message(int(reciepient.id), message=message.text)
