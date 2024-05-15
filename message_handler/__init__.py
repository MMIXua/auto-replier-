
import asyncio
import copy

import aiohttp
import markdown

from logger import log

from dtypes.message.statuses import BlankReplyMsgStatus, WaitingForSendMsgStatus, WaitingForReviewStatus, ReviewedMsgStatus
from dtypes.message.statuses import ErrorReviewingMsgStatus, ErrorGeneratingAnswer
from dtypes.message import Message

from agent import MultiAgent, ManagerAgent, ReviewAgent, CleanAgent

from config import MESSAGE_HANDLER_DELAY, API
from utils import clear


CONN_API = API["conn"]["entry"]


class MessageHandler:

    def __init__(self):
        self.log = log.bind(classname=self.__class__.__name__)
        self.http_client = None
        self.loop = None

    async def fill_blank_message(self, blank_message):
        self.log.info(f"Got {blank_message = }")

        try:
            http_client = aiohttp.ClientSession(loop=self.loop)

            agent = MultiAgent(
                entry_message_id=blank_message.reply_to_id,
                steps=[
                    CleanAgent(),
                    ManagerAgent(),
                    ReviewAgent()
                ]
            )

            self.log.debug(f"Trying to get ask message -> {blank_message.reply_to_id}")
            async with http_client.get(f"{CONN_API}/message", json={"id": blank_message.reply_to_id}) as response:
                message_response = await response.json()
            self.log.debug(f"Got response from getting ask message -> {message_response}")

            ask_message = Message(**message_response['message']) if "message" in message_response else None

            async with http_client.post(f"{CONN_API}/generate", json=clear(agent.to_dict())) as response:
                gpt_response = await response.json()

            if gpt_response["status"] != "ok" or not gpt_response["data"]["result"]:
                blank_message.status = str(ErrorGeneratingAnswer())

            else:
                cleaner_step = gpt_response["data"]["steps"][0]
                if cleaner_step["status"] == "ok" and cleaner_step["data"]["result"]:
                    ask_message.text = cleaner_step["data"]["result"]
                    self.log.debug(f"Trying to update ask message -> {ask_message}")
                    async with http_client.post(f"{CONN_API}/update_message", json=clear(ask_message.to_dict())) as response:
                        updated_ask_message_response = await response.json()
                    self.log.debug(f"Got response from updating review message -> {updated_ask_message_response}")

                for step in gpt_response["data"]["steps"]:
                    self.log.debug(f"Generating step: {blank_message} -> {step}")

                md = markdown.Markdown(extensions=["markdown_del_ins", "fenced_code"])
                blank_message.text = md.convert(gpt_response["data"]["result"])
                blank_message.set_status(WaitingForSendMsgStatus())

            async with http_client.post(f"{CONN_API}/update_message", json=clear(blank_message.to_dict())) as response:
                updated_message_response = await response.json()

            self.log.debug(f"Got updated_message_response -> {updated_message_response}")
            await http_client.close()

        except Exception as err:
            self.log.exception(err)

    async def review_message(self, review_message):
        self.log.info(f"Got {review_message = }")

        try:
            http_client = aiohttp.ClientSession(loop=self.loop)

            self.log.debug(f"Trying to get gpt answer message -> {review_message.reply_to_id}")
            async with http_client.get(f"{CONN_API}/message", json={"id": review_message.reply_to_id}) as response:
                message_response = await response.json()
            self.log.debug(f"Got response from getting gpt answer message -> {message_response}")

            if "message" not in message_response:
                review_message.set_status(ErrorReviewingMsgStatus())

                self.log.debug(f"Trying to update review message -> {review_message}")
                async with http_client.post(f"{CONN_API}/update_message", json=clear(review_message.to_dict())) as response:
                    updated_review_message_response = await response.json()
                self.log.debug(f"Got response from getting review message -> {updated_review_message_response}")

                return await http_client.close()

            target_message = Message(**message_response["message"])

            if target_message.reviewed:
                self.log.info(f"Cant review message {target_message} because it has already been reviewed")
                review_message.set_status(ReviewedMsgStatus())

            else:
                agent = MultiAgent(
                    entry_message_id=review_message.id,
                    steps=[
                        CleanAgent()
                    ]
                )

                async with http_client.post(f"{CONN_API}/generate", json=clear(agent.to_dict())) as response:
                    gpt_response = await response.json()

                if gpt_response["status"] == "ok" and gpt_response["data"]["result"]:
                    for step in gpt_response["data"]:
                        self.log.debug(f"Generating step: {review_message} -> {step}")

                    md = markdown.Markdown(extensions=["markdown_del_ins", "fenced_code"])
                    review_message.text = md.convert(gpt_response["data"]["result"])

                    self.log.debug(f"Trying to update review message -> {review_message}")
                    async with http_client.post(f"{CONN_API}/update_message", json=clear(review_message.to_dict())) as response:
                        updated_message_response = await response.json()
                    self.log.debug(f"Got response from updating review message -> {updated_message_response}")

                agent = MultiAgent(
                    entry_message_id=target_message.id,
                    steps=[
                        ReviewAgent(
                            review_message_id=review_message.id
                        )
                    ]
                )

                async with http_client.post(f"{CONN_API}/generate", json=clear(agent.to_dict())) as response:
                    gpt_response = await response.json()

                if gpt_response["status"] == "ok" and gpt_response["data"]["result"]:
                    for step in gpt_response["data"]:
                        self.log.debug(f"Generating step: {review_message} -> {step}")

                    md = markdown.Markdown(extensions=["markdown_del_ins", "fenced_code"])
                    target_message.text = md.convert(gpt_response["data"]["result"])
                    target_message.set_status(WaitingForSendMsgStatus())
                    target_message.reviewed = True

                    self.log.debug(f"Trying to update target message -> {target_message}")
                    async with http_client.post(f"{CONN_API}/update_message", json=clear(target_message.to_dict())) as response:
                        updated_message_response = await response.json()
                    self.log.debug(f"Got response from updating target message -> {updated_message_response}")

                    review_message.set_status(ReviewedMsgStatus())

                else:
                    review_message.status = str(ErrorGeneratingAnswer())

            self.log.debug(f"Trying to update review message -> {review_message}")
            async with http_client.post(f"{CONN_API}/update_message", json=clear(review_message.to_dict())) as response:
                updated_review_message_response = await response.json()
            self.log.debug(f"Got response from updating review message -> {updated_review_message_response}")

            return await http_client.close()

        except Exception as err:
            self.log.exception(err)

    async def listen_review_messages(self):
        while True:
            try:
                http_client = aiohttp.ClientSession(loop=self.loop)

                async with http_client.get(f"{CONN_API}/messages", json={
                    "status": str(WaitingForReviewStatus())
                }) as response:
                    messages_response = await response.json()

                await http_client.close()

                if messages_response["data"]:
                    review_messages = list(map(lambda x: Message(**x), messages_response["data"]))
                    self.log.debug(f"Got {len(review_messages)} review messages")

                    await asyncio.gather(*[self.review_message(review_message) for review_message in review_messages])

            except Exception as err:
                self.log.exception(err)

            await asyncio.sleep(MESSAGE_HANDLER_DELAY)

    async def listen_blank_messages(self):
        while True:
            try:
                http_client = aiohttp.ClientSession(loop=self.loop)

                async with http_client.get(f"{CONN_API}/messages", json={
                    "status": str(BlankReplyMsgStatus())
                }) as response:
                    messages_response = await response.json()

                await http_client.close()

                if messages_response["data"]:
                    blank_messages = list(map(lambda x: Message(**x), messages_response["data"]))
                    self.log.debug(f"Got {len(blank_messages)} blank messages")

                    await asyncio.gather(*[self.fill_blank_message(blank_message) for blank_message in blank_messages])

            except Exception as err:
                self.log.exception(err)

            await asyncio.sleep(MESSAGE_HANDLER_DELAY)

    def listen(self):
        loop = asyncio.new_event_loop()
        self.loop = loop
        loop.create_task(self.listen_review_messages())
        loop.run_until_complete(self.listen_blank_messages())
