
import click


@click.group()
def group():
    """Group for command"""


@group.command("run_app")
def _run_app():
    import config
    config.LOGS_PATH = config.LOGS_PATH.format(module="app")

    from app import run_app

    run_app()


@group.command("run_papp")
def _run_papp():
    import config
    config.LOGS_PATH = config.LOGS_PATH.format(module="papp")

    from app import run_papp

    run_papp()
