
from typing import Type

import motor.motor_asyncio as motor
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from dtypes.user import BaseUser, to_user_type
from dtypes.response import BaseResponse, ErrResponse, OkResponse
from dtypes.dialog import Dialog
from dtypes.message import Message

from utils.singleton import SingletonMeta

from logger import log
from config import MONGODB_URI


class Db(metaclass=SingletonMeta):
    def __init__(self):
        self.log = log.bind(classname=self.__class__.__name__)
        self.mongo_client = None
        self.db = None
        self.users_collection: AsyncIOMotorCollection = None
        self.dialogs_collection: AsyncIOMotorCollection = None
        self.messages_collection: AsyncIOMotorCollection = None
        self.gpt_threads_collection: AsyncIOMotorCollection = None
        self.config_collection: AsyncIOMotorCollection = None

    def connect(self):
        try:
            self.mongo_client = motor.AsyncIOMotorClient(MONGODB_URI)
            self.db: AsyncIOMotorDatabase = self.mongo_client.AutoReplies
            self.users_collection: AsyncIOMotorCollection = self.db.users
            self.dialogs_collection: AsyncIOMotorCollection = self.db.dialogs
            self.messages_collection: AsyncIOMotorCollection = self.db.messages
            self.gpt_threads_collection: AsyncIOMotorCollection = self.db.gpt_threads
            self.config_collection: AsyncIOMotorCollection = self.db.config
            self.log.info(f"Connected to db")

        except Exception as err:
            self.log.exception(err)
            self.log.critical(f"Cant connect to db")
            exit()

    async def is_user(self, user: Type[BaseUser]) -> bool:
        return True if await self.get_user(user.id) else False

    async def get_user(self, user_id: str) -> Type[BaseUser]:
        user_raw = await self.db.users.find_one({"id": user_id}, {"_id": 0})

        if not user_raw:
            self.log.debug(f"Coudn't get user -> {user_id}")
            return None

        user_type = to_user_type(user_raw['type'])
        del user_raw["type"]

        user = user_type(**user_raw)
        self.log.debug(f"Got user -> {user_id} -> {user}")
        return user

    async def get_users(self, _filter: dict) -> list[Type[BaseUser]]:
        users_raw = self.db.users.find(_filter, {"_id": 0})
        users = []

        async for user_raw in users_raw:
            user_type = to_user_type(user_raw['type'])
            del user_raw["type"]
            users.append(user_type(**user_raw))

        self.log.debug(f"Got users -> {_filter} -> {users}")
        return users

    async def add_user(self, user: Type[BaseUser]) -> Type[BaseResponse]:
        if await self.is_user(user):
            self.log.debug(f"Coundn't add user -> duplicate -> {user}")
            return ErrResponse("Duplicate user", data={
                "id": user.id
            })

        response = await self.db.users.insert_one(user.to_dict())
        self.log.debug(f"Added user -> {user}")
        return OkResponse(data={
            "db": str(response),
            "id": user.id
        })

    async def update_user(self, user: Type[BaseUser]) -> Type[BaseResponse]:
        response = await self.users_collection.update_one({"id": user.id}, {"$set": user.to_dict()}, True)
        self.log.debug(f"Updated user -> {user}")
        return OkResponse(data=str(response))

    async def is_dialog(self, dialog: Dialog) -> bool:
        return True if await self.get_dialog(dialog.id) else False

    async def get_dialog(self, dialog_id: str) -> Dialog:
        dialog_raw = await self.dialogs_collection.find_one({"id": dialog_id}, {"_id": 0})

        if not dialog_raw:
            self.log.debug(f"Coudn't get dialog -> {dialog_id} -> {dialog_id}")
            return None

        dialog = Dialog(**dialog_raw)
        self.log.debug(f"Got dialog -> {dialog_id} -> {dialog}")
        return dialog

    async def get_dialogs(self, _filter: dict) -> list[Dialog]:
        dialogs_raw = self.dialogs_collection.find(_filter, {"_id": 0})
        dialogs = []

        async for dialog_raw in dialogs_raw:
            dialogs.append(Dialog(**dialog_raw))

        self.log.debug(f"Got dialogs -> {_filter} -> {dialogs}")
        return dialogs

    async def add_dialog(self, dialog: Dialog) -> Type[BaseResponse]:
        if await self.is_dialog(dialog):
            self.log.debug(f"Coudn't add dialog -> duplicate -> {dialog}")
            return ErrResponse("Duplicate dialog", data={
                "id": dialog.id
            })

        response = await self.dialogs_collection.insert_one(dialog.to_dict())
        self.log.debug(f"Added dialog -> {dialog}")
        return OkResponse(data={
            "db": str(response),
            "id": dialog.id
        })

    async def update_dialog(self, dialog: Dialog) -> Type[BaseResponse]:
        response = await self.dialogs_collection.update_one({"id": dialog.id}, {"$set": dialog.to_dict()}, True)
        self.log.debug(f"Updated dialog -> {dialog}")
        return OkResponse(data=str(response))

    async def is_message(self, message: Message) -> bool:
        return True if await self.get_message(message.id) else False

    async def get_message(self, message_id: str) -> Message:
        message_raw = await self.messages_collection.find_one({"id": message_id}, {"_id": 0})

        if not message_raw:
            self.log.debug(f"Coudn't get message -> {message_id} -> {message_id}")
            return None

        message = Message(**message_raw)
        self.log.debug(f"Got message -> {message_id} -> {message}")
        return message

    async def get_messages(self, _filter) -> list[Message]:
        messages_raw = self.messages_collection.find(_filter, {"_id": 0})
        messages = []

        async for messages_raw in messages_raw:
            messages.append(Message(**messages_raw))

        self.log.debug(f"Got messages -> {_filter} -> {messages}")
        return messages

    async def add_message(self, message: Message) -> Type[BaseResponse]:
        if await self.is_message(message):
            self.log.debug(f"Coudn't add message -> duplicate -> {message}")
            return ErrResponse("Duplicate message", data={
                "id": message.id
            })

        response = await self.messages_collection.insert_one(message.to_dict())
        self.log.debug(f"Added message -> {message}")
        return OkResponse(data={
            "db": str(response),
            "id": message.id
        })

    async def update_message(self, message: Message) -> Type[BaseResponse]:
        response = await self.messages_collection.update_one({"id": message.id}, {"$set": message.to_dict()}, True)
        self.log.debug(f"Updated message -> {message}")
        return OkResponse(data=str(response))

    async def get_gpt_thread_id(self, dialog_id: str):
        gpt_thread = await self.gpt_threads_collection.find_one({"dialog_id": dialog_id}, {"_id": 0})

        if not gpt_thread:
            self.log.debug(f"Coudn't get gpt_thread_id by dialog_id -> {dialog_id}")
            return None

        thread_id = gpt_thread["id"]
        self.log.debug(f"Got gpt_thread_id by dialog_id -> {dialog_id}")
        return thread_id

    async def is_gpt_thread(self, dialog_id):
        return True if await self.get_gpt_thread_id(dialog_id) else False

    async def add_gpt_thread_id(self, dialog_id, gpt_thread_id):
        data = {"dialog_id": dialog_id, "id": gpt_thread_id}
        if await self.is_gpt_thread(dialog_id):
            self.log.debug(f"Cound't add gpt_thread_id -> duplicate -> {data}")
            return ErrResponse("Duplicate message")

        response = await self.gpt_threads_collection.insert_one(data)
        self.log.debug(f"Added gpt_thread_id -> duplicate -> {data}")
        return OkResponse(data=str(response))

    async def get_config(self, config_id):
        config = await self.config_collection.find_one({"id": config_id}, {"_id": 0})

        if not config:
            self.log.debug(f"Coudn't get config -> {config_id}")
            return None

        self.log.debug(f"Got config -> {config_id} -> {config}")
        return config

    async def is_config(self, config_id):
        return True if await self.get_config(config_id) else False

    async def add_config(self, config):
        if await self.is_config(config["id"]):
            self.log.debug(f"Cound't add config -> duplicate -> {config}")
            return ErrResponse("Duplicate message")

        response = await self.config_collection.insert_one(config)
        self.log.debug(f"Added config -> duplicate -> {config}")
        return OkResponse(data=str(response))

    async def update_config(self, config):
        response = await self.config_collection.update_one({"id": config["id"]}, {"$set": config}, True)
        self.log.debug(f"Updated config -> {config}")
        return OkResponse(data=str(response))


db = Db()
db.connect()
