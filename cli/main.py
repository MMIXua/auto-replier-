import os

import click


procs = [
    "run_app",
    "run_papp",
    "run_handler",
    "run_updater",
] + [
    f"run_source {source}" for source in ["gmail", "telegram", "whatsapp"]
]


@click.group()
def group():
    """Group for command"""


@group.command("start")
def run_all():
    command = "screen -dmS {name} python main.py {proc}"

    for proc in procs:
        s = command.format(name=proc.split()[-1].split("_")[-1], proc=proc)
        print(s)
        os.system(s)


@group.command("stop")
def stop_all():
    command = "screen -S {name} -X quit"

    for proc in procs:
        s = command.format(name=proc.split()[-1].split("_")[-1])
        print(s)
        os.system(s)
