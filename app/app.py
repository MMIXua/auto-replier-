import copy
import random
import uuid

from fastapi import FastAPI
import uvicorn

from dtypes.response import OkResponse, ErrResponse
from dtypes.user import to_user
from dtypes.dialog import to_dialog
from dtypes.message import to_message
from dtypes.message.statuses import BlankReplyMsgStatus
from agent import to_agent, MultiAgent

from utils import clear, string_to_uuid
from db import db

from config import API

from .models import SearchUserModel, SearchUsersModel, UserModel
from .models import SearchDialogModel, SearchDialogsModel, DialogModel
from .models import SearchMessageModel, SearchMessagesModel, MessageModel
from .models import SearchConfigModel, ConfigModel
from .models import GenerateModel


app = FastAPI()


@app.get("/ping")
async def ping():
    try:
        return OkResponse().to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.get("/user")
async def get_user(search_model: SearchUserModel):
    try:
        user = await db.get_user(search_model.id)

        return OkResponse(data=user).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.get("/users")
async def get_users(search_model: SearchUsersModel):
    try:
        users = await db.get_users(clear(search_model.model_dump(mode="python")))

        return OkResponse(data=users).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.post("/user")
async def add_user(model: UserModel):
    try:
        data = model.model_dump(mode='python')

        if data.get("id") is None:
            data.update({"id": string_to_uuid(data["link"])})

        user = to_user(data)

        return (await db.add_user(user)).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.post("/update_user")
async def update_user(model: UserModel):
    try:
        user = to_user(model.model_dump(mode='python'))
        return (await db.update_user(user)).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.get("/dialog")
async def get_dialog(search_model: SearchDialogModel):
    try:
        dialog = await db.get_dialog(search_model.id)

        return OkResponse(data=dialog).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.get("/dialog/messages")
async def get_dialog_messages(search_model: SearchDialogModel):
    try:
        dialog = await db.get_dialog(search_model.id)

        if not dialog:
            return ErrResponse(description="No such dialog").to_dict()

        messages = await db.get_messages({
            "dialog_id": dialog.id
        })

        return OkResponse(data=messages).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.get("/dialogs")
async def get_dialogs(search_model: SearchDialogsModel):
    try:
        dialogs = await db.get_dialogs(clear(search_model.model_dump(mode="python")))

        return OkResponse(data=dialogs).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.post("/dialog")
async def add_dialog(model: DialogModel):
    try:
        dialog = to_dialog(model.model_dump(mode="python"))
        dialog.gpt_face = random.choice((await db.get_config("main"))["faces"])

        return (await db.add_dialog(dialog)).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.post("/update_dialog")
async def update_dialog(model: DialogModel):
    try:
        dialog = to_dialog(model.model_dump(mode="python"))

        return (await db.update_dialog(dialog)).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.get("/message")
async def get_message(search_model: SearchMessageModel):
    try:
        message = await db.get_message(search_model.id)

        return OkResponse(data=message).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.get("/messages")
async def get_messages(search_model: SearchMessagesModel):
    try:
        messages = await db.get_messages(clear(search_model.model_dump(mode="python")))

        return OkResponse(data=messages).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.post("/message")
async def add_message(model: MessageModel):
    try:
        data = model.model_dump(mode='python')

        if data.get("id") is None:
            data.update({"id": '_'.join((data["sender_id"], uuid.uuid4().hex[:8]))})

        make_blank_reply = data.pop("make_blank_reply")

        message = to_message(data)

        if message.sender_id != "bot":
            user = await db.get_user(message.sender_id)

            if not user.first_message:
                user.first_message = message.date

            user.last_message = message.date
            await db.update_user(user)

        response = await db.add_message(message)
        reply_response = None

        if make_blank_reply:
            reply_message = copy.deepcopy(message)
            reply_message.id = '_'.join((message.id, "reply"))
            reply_message.reply_to_id = message.id
            reply_message.sender_id = "bot"
            reply_message.status = str(BlankReplyMsgStatus())
            reply_message.text = None

            reply_response = (await db.add_message(reply_message)).to_dict()

        response.data.update({
            "make_blank_reply": reply_response
        })

        return response.to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.post("/update_message")
async def update_message(model: MessageModel):
    try:
        data = model.model_dump(mode='python')

        del data["make_blank_reply"]
        message = to_message(data)

        return (await db.update_message(message)).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.post("/generate")
async def generate_answer(model: GenerateModel):
    try:
        data = model.model_dump(mode='python')

        steps = [to_agent(step) for step in data['steps']]
        agent = MultiAgent(
            entry_message_id=data['entry_message_id'],
            steps=steps
        )

        entry_message = await db.get_message(data['entry_message_id'])
        return (await agent.run(entry_message)).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.get("/config")
async def get_config(search_model: SearchConfigModel):
    try:
        config = await db.get_config(search_model.id)

        return OkResponse(data=config).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.post("/config")
async def add_config(model: ConfigModel):
    try:
        config = model.model_dump(mode="python")
        config["data"].update({"id": config["id"]})
        config = config["data"]

        return (await db.add_config(config)).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


@app.post("/update_config")
async def update_dialog(model: ConfigModel):
    try:
        config = model.model_dump(mode="python")
        config["data"].update({"id": config["id"]})
        config = config["data"]

        return (await db.update_config(config)).to_dict()

    except Exception as err:
        return ErrResponse(description=str(err)).to_dict()


def run_app():
    config = uvicorn.Config(
        "app:app",
        port=API["conn"]["port"],
        host=API["conn"]["host"],
        log_level="debug"
    )
    server = uvicorn.Server(config)
    server.run()
