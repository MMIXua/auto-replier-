import os

import click
from telethon.sync import TelegramClient as TClient

from config import TELEGRAM_SESSIONS_PATH


@click.group()
def group():
    """Group for command"""


@group.command("authtg")
@click.argument('phone', type=str)
@click.argument('api_id', type=str)
@click.argument('api_hash', type=str)
def gen_session(phone, api_id, api_hash):
    import config
    config.LOGS_PATH = config.LOGS_PATH.format(module="authtg")

    session_path = os.path.join(TELEGRAM_SESSIONS_PATH, f"{phone}.session")

    client = TClient(session_path, api_id, api_hash)
    client.start(phone=phone)

    print(f"Generated telegram session -> {session_path}")
