
import copy
import typing
from dtypes.message import Message
from dtypes.response import OkResponse, ErrResponse
from utils.jsonify import Jsonified
from utils import remove_gpt_file_marker

from db import db

from . import gpt


class BaseAgent(Jsonified):
    name: str = "base"
    is_one_shot: bool = True

    def __init__(self):
        self.name = self.name

        self.fields = ["name"]

    async def get_thread_id(self, message: Message):
        if self.is_one_shot:
            return True, (await gpt.create_gpt_thread()).id

        dialog_id = message.dialog_id

        if await db.is_gpt_thread(dialog_id):
            return False, await db.get_gpt_thread_id(dialog_id)

        thread_id = (await gpt.create_gpt_thread()).id
        await db.add_gpt_thread_id(dialog_id, thread_id)

        return True, thread_id

    async def get_prompt_in_dialog(self, message: Message):
        return await self.get_prompt_new_dialog(message)

    async def get_prompt_new_dialog(self, message: Message):
        return ""

    async def get_prompt(self, message: Message, is_new_dialog: bool):
        if is_new_dialog:
            return await self.get_prompt_new_dialog(message)

        else:
            return await self.get_prompt_in_dialog(message)

    def filter(self, string):
        filters = [
            remove_gpt_file_marker
        ]

        for _filter in filters:
            string = _filter(string)

        return string

    async def is_generate(self, message: Message):
        return True

    async def run(self, message: Message):
        try:
            if not self.is_generate(message):
                return OkResponse(
                    data={
                        "step": self.name,
                        "result": message.text
                    }
                )

            is_new_dialog, thread_id = await self.get_thread_id(message)
            prompt = await self.get_prompt(message, is_new_dialog)

            await gpt.create_message(thread_id, prompt)

            config = await db.get_config("main")
            run_id = await gpt.send_to_assistant(thread_id, config["assistants"][self.name])
            resp = await gpt.wait_for_response(thread_id, run_id, config)

            if resp:
                resp = self.filter(resp)

            return OkResponse(
                data={
                    "step": self.name,
                    "result": resp
                }
            )

        except Exception as err:
            return ErrResponse(
                data={
                    "step": self.name,
                    "result": None
                },
                description=str(err)
            )


class MultiAgent(Jsonified):
    steps: list[typing.Type[BaseAgent]]

    def __init__(self, entry_message_id: str, steps: list[typing.Type[BaseAgent]]):
        self.entry_message_id = entry_message_id
        self.steps = steps

        self.fields = ["entry_message_id", "steps"]

    async def run(self, entry_message: Message):
        if not entry_message:
            return ErrResponse(description="no entry message")

        temp_entry_message = copy.deepcopy(entry_message)
        steps = []

        for step in self.steps:
            agent_response = await step.run(temp_entry_message)
            steps.append(agent_response)

            if agent_response.status == "ok" and agent_response.data["result"]:
                temp_entry_message.text = agent_response.data["result"]

        is_ok = False

        for step in steps:
            if step.status == "ok" and step.data["result"]:
                is_ok = True
                break

        if is_ok:
            return OkResponse(
                data={
                    "steps": steps,
                    "result": temp_entry_message.text
                }
            )

        return ErrResponse(
            data={
                "steps": steps,
                "result": None
            }
        )


from .agent import ManagerAgent, ReviewAgent, CleanAgent
from .utils import to_agent
