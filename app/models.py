
from pydantic import BaseModel, Field
from typing import Literal, Optional


user_type = Literal["client", "bot"]
source_type = Literal["gmail"]
id_field = Field(..., min_length=3, max_length=500)


class UserModel(BaseModel):
    id: str = None
    type: str = user_type
    source: str = source_type
    link: str
    first_message: int = 0
    last_message: int = 0
    firstname: str = None
    phone: str = None


class SearchUsersModel(BaseModel):
    id: dict | str = None
    type: str = None
    source: str = None


class SearchUserModel(BaseModel):
    id: str = id_field


class DialogModel(BaseModel):
    id: str = id_field
    source: str = source_type
    participants: list[str] = []


class SearchDialogModel(BaseModel):
    id: str = id_field


class SearchDialogsModel(BaseModel):
    id: str = None
    participants: list[str] = None


class MessageModel(BaseModel):
    id: str = None
    reply_to_id: str = None
    reviewer_id: str = None
    reviewed: bool = None
    dialog_id: str = id_field
    sender_id: str = id_field
    source: str = source_type
    source_link: str = None
    make_blank_reply: bool = False
    status: str
    subject: str = None
    text: str
    date: int = None


class SearchMessageModel(BaseModel):
    id: str = id_field


class SearchMessagesModel(BaseModel):
    id: str = None
    dialog_id: str = None
    sender_id: str = None
    text: str = None
    source: str = None
    status: str = None


class ManagerAssistantModel(BaseModel):
    message_id: str = id_field


class CleanerAssistantModel(BaseModel):
    message_id: str = id_field


class ReviewAssistantModel(BaseModel):
    target_id: str = id_field
    review_id: str = id_field


class SearchConfigModel(BaseModel):
    id: str = id_field


class ConfigModel(BaseModel):
    id: str = id_field
    data: dict


class GenerateModel(BaseModel):
    entry_message_id: str = id_field
    steps: list
