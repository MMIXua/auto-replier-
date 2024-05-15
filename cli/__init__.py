
from . import run_app, run_source, run_handler, run_updater, database, authtg, main

import click

execute = click.CommandCollection(
    sources=[
        run_app.group,
        run_source.group,
        run_handler.group,
        run_updater.group,
        database.group,
        authtg.group,
        main.group
    ],
    help='Use "main.py <command> -h/--help" to see more info about a command',
)
