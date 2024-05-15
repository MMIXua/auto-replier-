
from fastapi import FastAPI, Request

from config import API
import uvicorn


app = FastAPI()


async def run_app(callback):

    @app.post("/")
    async def webhook(request: Request):
        data = await request.json()

        await callback(data)

    config = uvicorn.Config(
        app,
        port=API["wp"]["port"],
        host=API["wp"]["host"],
        log_level="debug",
    )
    server = uvicorn.Server(config)
    await server.serve()
