
import os

import asyncio
import random

import aiohttp

from glob import glob

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response, FileResponse

from db import db
from config import API, HTML_TEMPLATES_PATH, STATIC_DIR
import uvicorn

from dtypes.message.statuses import WaitingForSendMsgStatus


papp = FastAPI()

templates = Jinja2Templates(directory=HTML_TEMPLATES_PATH)
WP_HOOK_TOKEN = "12345"


@papp.get("/ping")
async def ping():
    try:
        return "ok"

    except Exception as err:
        return str(err)


@papp.get("/send/{message_id}")
async def ping(request: Request, message_id: str):
    message = await db.get_message(message_id)

    if not message:
        status = "no_message"
        text = ""

    elif message.reviewed:
        status = str(message.status)
        text = message.text

    else:
        status = str(WaitingForSendMsgStatus())
        message.set_status(WaitingForSendMsgStatus())
        message.reviewed = True
        await db.update_message(message)
        text = message.text

    return templates.TemplateResponse(
        request=request, name="send_message.html", context={
            "status": status,
            "message_id": message_id,
            "text": text
        }
    )


@papp.get("/view")
async def view(request: Request, hls: str):

    ebla_templates = list(map(
        lambda x: f"{API['pub']['entry']}/files/{x.split('/')[-1]}",
        glob(os.path.join(STATIC_DIR, "eblo*"))
    ))
    ebla = random.choices(ebla_templates, k=random.randint(10, 20))

    return templates.TemplateResponse(
        request=request, name="player.html", context={
            "hls": hls,
            "ebla": ebla
        }
    )


@papp.get("/files/{file_name}")
async def file(file_name: str):
    file_path = os.path.join(STATIC_DIR, file_name)

    if not os.path.isfile(file_path):
        return Response(status_code=404)

    return FileResponse(path=file_path, filename=file_name.split("/")[-1], media_type='multipart/form-data')


@papp.get("/wphook")
def subscribe(request: Request):
    if request.query_params.get('hub.verify_token') == WP_HOOK_TOKEN:
        return int(request.query_params.get('hub.challenge'))

    return "Authentication failed. Invalid Token."


async def forward(data):
    http = aiohttp.ClientSession(loop=asyncio.get_running_loop())

    async with http.post(f"{API['wp']['entry']}", json=data) as response:
        pass

    await http.close()


@papp.post("/wphook")
async def callback(request: Request):
    data = await request.json()

    asyncio.create_task(forward(data))

    return {"status": "success"}, 200


def run_papp():
    config = uvicorn.Config(
        "app:papp",
        port=API["pub"]["port"],
        host=API["pub"]["host"],
        log_level="debug",
    )
    server = uvicorn.Server(config)
    server.run()
