
import asyncio
import functools
import json

from openai.types.beta.threads import RequiredActionFunctionToolCall
import time

from config import GPT_TIMEOUT

from logger import log

from openai import AsyncClient
from config import GPT_API_KEY


GPT = AsyncClient(api_key=GPT_API_KEY)
gpt_log = log.bind(classname="GPT")


async def create_gpt_thread():
    try:
        thread = await GPT.beta.threads.create()
        gpt_log.debug(f"Created thread -> {thread}")

        return thread

    except Exception as err:
        gpt_log.exception(err)
        gpt_log.error(f"Coudn't create thread")

        return None


async def create_message(thread_id: str, prompt: str) -> None:
    _prompt = prompt.replace("\n", "\\n")

    try:
        message = await GPT.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt
        )
        gpt_log.debug(f"Crated message -> {thread_id} -> {_prompt} -> {message}")

        return message

    except Exception as err:
        gpt_log.exception(err)
        gpt_log.error(f"Coudn't create message -> {thread_id} -> {_prompt}")

        return None


async def send_to_assistant(thread_id: str, assistant_id: str) -> str:
    try:
        run = await GPT.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        gpt_log.debug(f"Sent to assistant -> {thread_id} -> {run}")

        return run.id

    except Exception as err:
        gpt_log.exception(err)
        gpt_log.error(f"Coudn't send to assistant -> {thread_id}")

        return None


def submit_tool_outputs(tool_call: RequiredActionFunctionToolCall, dynamic_data: dict):
    data = json.loads(tool_call.function.arguments)

    response = None

    if tool_call.function.name == "get_creds":
        bank_name = data.get("bank").lower()
        response = "This bank is not powered by us"

        for payment in dynamic_data["payments"]:
            if bank_name in payment["keys"]:
                del payment["keys"]
                del payment["name"]

                response = payment

    elif tool_call.function.name == "get_creds_list":
        response = [{
            "name": payment["name"],
            "value": payment["value"]
        } for payment in dynamic_data["payments"]]

    return {
        "tool_call_id": tool_call.id,
        "output": json.dumps(response) if response else "Not enought information"
    }


async def wait_for_response(thread_id: str, run_id: str, dynamic_data: dict) -> str | None:
    try:
        status = None
        time_start = time.time()

        while not status or status != "completed":
            run = await GPT.beta.threads.runs.retrieve(run_id=run_id, thread_id=thread_id)

            if run.required_action:
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = list(map(functools.partial(submit_tool_outputs, dynamic_data=dynamic_data), tool_calls))
                gpt_log.debug(f"Answered tool cals -> {tool_calls} -> {tool_outputs}")

                run = await GPT.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs
                )

            status = run.status
            gpt_log.debug(f"Waiting for response -> {thread_id} -> {run_id} -> {status}")
            await asyncio.sleep(3)

            if time.time() - time_start >= GPT_TIMEOUT:
                return gpt_log.debug(f"Got timeout")

        response = await GPT.beta.threads.messages.list(
            thread_id=thread_id
        )

        gpt_log.debug(f"Got response -> {response}")

        if response.data:
            return response.data[0].content[0].text.value

        return None

    except Exception as err:
        gpt_log.exception(err)
        gpt_log.error(f"Coudn't wait for response -> {thread_id} -> {run_id}")

        return None
