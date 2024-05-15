
import click

import config


@click.group()
def group():
    """Group for command"""


@group.command("run_source")
@click.argument('source_type', type=str)
def run_source(source_type):
    config.LOGS_PATH = config.LOGS_PATH.format(module=source_type)

    from source_listener import to_source_listener_type

    source_listener_type = to_source_listener_type(source_type)

    if not source_listener_type:
        return print("Wrong source listener type")

    source_listener = source_listener_type()
    source_listener.listen()
