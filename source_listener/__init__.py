import time
from typing import Type

import asyncio
import aiohttp
from logger import log

from dtypes.message import Message
from dtypes.dialog import Dialog
from dtypes.user import to_user, BaseUser
from dtypes.message.statuses import ReadMsgStatus, WaitingForSendMsgStatus, SentMsgStatus, ReceivedMsgStatus, ErrorSendingMsgStatus
from dtypes.source_type import BaseSourceType

from .output import ListenerOutput

from utils import clear

from config import API

CONN_API = API["conn"]["entry"]


class BaseSourceListener:
    source_type = BaseSourceType()
    client = None
    incoming_delay = 0
    outcoming_delay = 0
    running: bool

    def __init__(self):
        self.loop = None
        self.client = None
        self.running = False
        self.semaphore = asyncio.Semaphore(10)
        self.log = log.bind(classname=self.__class__.__name__)
        self.incoming_delay = self.incoming_delay
        self.outcoming_delay = self.outcoming_delay

    async def find_recipient(self, recipients: list[str]) -> Type[BaseUser]:
        for recipient in recipients:
            if recipient != "bot":
                http = aiohttp.ClientSession(loop=asyncio.get_running_loop())

                async with http.get(f"{CONN_API}/user", json={"id": recipient}) as response:
                    user_response = await response.json()

                await http.close()

                self.log.debug(f"Got user_response -> {user_response}")
                recipient = to_user(user_response["user"])
                return recipient

    async def get_reviewers(self):
        try:
            http = aiohttp.ClientSession(loop=asyncio.get_running_loop())

            async with http.get(f"{CONN_API}/config", json={"id": "main"}) as response:
                config_response = await response.json()

            self.log.info(f"Got response from config -> {config_response}")

            reviewers = list(map(lambda x: x["id"], config_response["data"]["reviewers"]))

            async with http.get(f"{CONN_API}/users", json={"id": {"$in": reviewers}, "type": "reviewer"}) as response:
                users_response = await response.json()

            await http.close()

            self.log.info(f"Got users_response -> {users_response}")
            reviewers = list(map(to_user, users_response["data"])) if users_response["data"] else []
            return reviewers

        except Exception as err:
            self.log.exception(err)
            self.log.error(f"Got error while getting reviewers")
            return []

    async def _connect(self):
        pass

    async def connect(self):
        try:
            await self._connect()
            self.log.info(f"Connected to source")

        except Exception as err:
            self.log.exception(err)
            self.log.critical(f"Cant connect to source")

    async def _get_outcoming_messages(self) -> list[Message]:
        http = aiohttp.ClientSession(loop=asyncio.get_running_loop())
        async with http.get(f"{CONN_API}/messages", json={
            "sender_id": "bot",
            "status": str(WaitingForSendMsgStatus()),
            "source": str(self.source_type)
        }) as response:
            messages_response = await response.json()

        self.log.debug(f"Got messages_response -> {messages_response}")

        messages = list(map(lambda x: Message(**x), messages_response["data"])) if messages_response["data"] else []

        for message in messages:
            message.set_status(ReadMsgStatus())

            async with http.post(f"{CONN_API}/update_message", json=clear(message.to_dict())) as response:
                update_message_response = await response.json()

            self.log.debug(f"Got update_message_response -> {update_message_response}")

            await self.send_message(message)

        await http.close()
        return messages

    async def get_outcoming_messages(self) -> list[Message]:
        try:
            messages = await self._get_outcoming_messages()
            self.log.debug(f"Got {len(messages)} outcoming messages")

        except Exception as err:
            self.log.exception(err)
            self.log.error(f"Cant get outcoming messages")
            messages = []

        self.log.debug(f"Processed {len(messages)} outcoming messages")

        return messages

    async def _send_review_message(self, recipient: Type[BaseUser], client: Type[BaseUser], message: Message, ask_message: Message, dialog: Dialog):
        pass

    async def _send_message(self, recipient: Type[BaseUser], message: Message, ask_message: Message, dialog: Dialog):
        pass

    async def send_message(self, message: Message):
        try:
            http = aiohttp.ClientSession(loop=asyncio.get_running_loop())

            async with http.get(f"{CONN_API}/dialog", json={"id": message.dialog_id}) as response:
                dialog_response = await response.json()

            self.log.debug(f"Got dialog_response -> {dialog_response}")
            dialog = Dialog(**dialog_response["dialog"])

            ask_message = None

            if message.reply_to_id:
                self.log.debug(f"Trying to get ask_message -> {message.reply_to_id}")
                async with http.get(f"{CONN_API}/message", json={"id": message.reply_to_id}) as response:
                    ask_message_response = await response.json()

                self.log.debug(f"Got ask_message response -> {ask_message_response}")
                if "message" in ask_message_response:
                    ask_message = Message(**ask_message_response["message"])

            recipient = await self.find_recipient(dialog.participants)

            try:
                if message.reviewer_id:
                    self.log.debug(f"Trying to get reviewer -> {message.reviewer_id}")
                    async with http.get(f"{CONN_API}/user", json={"id": message.reviewer_id}) as response:
                        reviewer_response = await response.json()

                    self.log.debug(f"Got reviewer response -> {reviewer_response}")

                    if "user" in reviewer_response:
                        reviewer = to_user(reviewer_response["user"])

                        if "duplicate" in message.id:
                            await self._send_message(reviewer, message, ask_message, dialog)

                        else:
                            await self._send_review_message(reviewer, recipient, message, ask_message, dialog)

                    else:
                        self.log.warning(f"Cant find user in reviewer_response -> {reviewer_response}")

                elif message.reviewed:
                    message.date = round(time.time())
                    async with http.post(f"{CONN_API}/update_message", json=clear(message.to_dict())) as response:
                        update_message_response = await response.json()

                    self.log.debug(f"Got update_message_response -> {update_message_response}")

                    await self._send_message(recipient, message, ask_message, dialog)

                    review_message = Message(**message.to_dict())
                    review_message.status = str(WaitingForSendMsgStatus())

                    for reviewer in await self.get_reviewers():
                        review_message.id += f"_{reviewer.id}_duplicate"
                        review_message.reviewer_id = reviewer.id
                        review_message.source = reviewer.source

                        review_message_data = clear(review_message.to_dict())
                        self.log.debug(f"Trying to add duplicate message -> {review_message_data}")
                        async with http.post(f"{CONN_API}/message", json=review_message_data) as response:
                            message_response = await response.json()

                        self.log.info(f"Got response from adding duplicate message -> {message_response}")

                message.set_status(SentMsgStatus())

            except Exception as err:
                self.log.exception(err)
                self.log.error(f"Got unexpected error while sending message")

                message.set_status(ErrorSendingMsgStatus())

            async with http.post(f"{CONN_API}/update_message", json=clear(message.to_dict())) as response:
                update_message_response = await response.json()

            self.log.debug(f"Got update_message_response -> {update_message_response}")
            self.log.info(f"Sent message -> {message} -> {recipient}")

            await http.close()

            if not ask_message or message.reviewer_id:
                return

            http = aiohttp.ClientSession(loop=asyncio.get_running_loop())

            for reviewer in await self.get_reviewers():
                review_message = Message(**message.to_dict())
                review_message.id += f"_{reviewer.id}_forreview"
                review_message.reviewer_id = reviewer.id
                review_message.status = str(WaitingForSendMsgStatus())
                review_message.source = reviewer.source

                review_message_data = clear(review_message.to_dict())

                self.log.debug(f"Trying to add for_review message -> {review_message_data}")
                async with http.post(f"{CONN_API}/message", json=review_message_data) as response:
                    message_response = await response.json()

                self.log.info(f"Got response from adding for_review message -> {message_response}")

            await http.close()
        except Exception as err:
            self.log.exception(err)
            self.log.error(f"Cant send message -> {message}")

    async def delay_outcoming(self):
        return await asyncio.sleep(self.outcoming_delay)

    async def listen_outcoming_messages(self):
        while self.running:
            await self.get_outcoming_messages()
            await self.delay_outcoming()

    async def _get_incoming_messages(self) -> list[ListenerOutput]:
        return []

    async def get_incoming_messages(self) -> list[ListenerOutput]:
        try:
            messages = await self._get_incoming_messages()
            self.log.debug(f"Got {len(messages)} incoming messages")

        except Exception as err:
            self.log.exception(err)
            self.log.error("Cant get incoming messages")

            messages = []

        for message in messages:
            await self.save_message(message)

        self.log.debug(f"Processed {len(messages)} incoming messages")

        return messages

    async def _save_message(self, data: ListenerOutput):
        data = data.to_dict()

        message_id = data.pop("message_id")
        message_text = data.pop("text")
        source_link = data.pop("source_link") if "source_link" in data else None
        subject = data.pop("subject") if "subject" in data else "UNDETERMINATED"

        user_data = clear(data)
        user_data.update({"type": "client", "source": str(self.source_type)})

        http = aiohttp.ClientSession(loop=asyncio.get_running_loop())

        self.log.debug(f"Trying to add user -> {user_data}")
        async with http.post(f"{CONN_API}/user", json=user_data) as response:
            user_response = await response.json()
        self.log.info(f"Got response from adding user -> {user_response}")

        dialog_data = {
            "id": user_response["data"]["id"],
            "participants": [user_response["data"]["id"], "bot"],
            "source": str(self.source_type),
        }

        self.log.debug(f"Trying to add dialog -> {dialog_data}")
        async with http.post(f"{CONN_API}/dialog", json=dialog_data) as response:
            dialog_response = await response.json()

        self.log.info(f"Got response from adding dialog -> {dialog_response}")

        message = Message(**{
            "id": '_'.join((dialog_response["data"]["id"], message_id)),
            "dialog_id": dialog_response["data"]["id"],
            "sender_id": user_response["data"]["id"],
            "source": str(self.source_type),
            "status": str(ReceivedMsgStatus()),
            "text": message_text,
            "subject": subject,
            "source_link": source_link,
            "date": round(time.time())
        })

        message_data = message.to_dict()
        message_data.update({"make_blank_reply": True})
        message_data = clear(message_data)

        self.log.debug(f"Trying to add message -> {message_data}")
        async with http.post(f"{CONN_API}/message", json=message_data) as response:
            message_response = await response.json()

        self.log.info(f"Got response from adding message -> {message_response}")
        return await http.close()

    async def save_message(self, message: dict):
        try:
            await self._save_message(message)

        except Exception as err:
            self.log.exception(err)
            self.log.error(f"Cant save message -> {message}")

    async def delay_incoming(self):
        return await asyncio.sleep(self.incoming_delay)

    async def listen_incoming_messages(self):
        while self.running:
            await self.get_incoming_messages()
            await self.delay_incoming()

    def listen(self):
        self.running = True

        self.log.debug(f"Starting listeners")
        self.loop = asyncio.new_event_loop()

        self.loop.run_until_complete(self.connect())
        self.log.debug(f"Started outcoming messages listener")

        self.loop.create_task(self.listen_outcoming_messages())
        self.log.debug(f"Started incoming messages listener")

        self.loop.run_until_complete(self.listen_incoming_messages())
        self.loop.close()


from .gmail import GmailSourceListener
from .telegram import TelegramSourceListener
from .whatsapp import WhatsappSourceListener
from .utils import to_source_listener_type
