import asyncio

import click


@click.group()
def group():
    """Group for command"""


async def clear(db, ask=True):
    if ask and input(f"Enter \"Yes\" to clear all database: ") != "Yes":
        return

    tables = [
        db.users_collection, db.messages_collection,
        db.dialogs_collection, db.gpt_threads_collection
    ]

    for table in tables:
        print(f"Removing table: {table}")
        await table.drop()

    print(f"Cleared database")


@group.command("db")
@click.argument('func_name', type=str)
def run_db_command(func_name):
    import config
    config.LOGS_PATH = config.LOGS_PATH.format(module="dbutils")

    from db import db

    funcs = {
        "clear": clear
    }

    func = funcs.get(func_name)

    if not func:
        return print(f"You entered wrong func -> {func_name}\nAvaible: {list(funcs)}")

    return asyncio.run(func(db))
