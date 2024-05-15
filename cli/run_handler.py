
import click


@click.group()
def group():
    """Group for command"""


@group.command("run_handler")
def run_handler():
    import config
    config.LOGS_PATH = config.LOGS_PATH.format(module="msg_handler")

    from message_handler import MessageHandler

    msg_handler = MessageHandler()
    msg_handler.listen()
