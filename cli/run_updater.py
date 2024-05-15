
import click


@click.group()
def group():
    """Group for command"""


@group.command("run_updater")
def run_updater():
    import config
    config.LOGS_PATH = config.LOGS_PATH.format(module="updater")

    from updater import Updater

    updater = Updater()
    updater.listen()
