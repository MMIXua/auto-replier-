
from . import BaseAgent, gpt

from dtypes.message import Message
from config import GPT_ASK_MESSAGE, GPT_REVIEW_MESSAGE
from db import db


class ManagerAgent(BaseAgent):
    name: str = "manager"
    is_one_shot: bool = False

    async def get_prompt_new_dialog(self, message: Message):
        sender = await db.get_user(message.sender_id)
        dialog = await db.get_dialog(message.dialog_id)

        return GPT_ASK_MESSAGE.format(
            client_name=sender.firstname,
            bot_firstname=dialog.gpt_face["firstname"],
            bot_lastname=dialog.gpt_face["lastname"],
            bot_age=dialog.gpt_face["age"],
            bot_sex=dialog.gpt_face["sex"],
            subject=message.subject,
            ask=message.text
        )

    async def get_prompt_in_dialog(self, message: Message):
        return f"ASK: {message.text}"


class ReviewAgent(BaseAgent):
    name: str = "reviewer"
    is_one_shot: bool = True

    def __init__(self, *args, review_message_id=None, **kwargs):
        BaseAgent.__init__(self, *args, **kwargs)

        self.review_message_id = review_message_id
        self.fields.append("review_message_id")

    async def get_prompt_new_dialog(self, message: Message):

        if self.review_message_id:
            review_message = await db.get_message(self.review_message_id)
            prompt = review_message.text if review_message else "do nothing"

        else:
            rules = [
                'Remove closing greeting like: "З повагою", "Best regards" etc.',
                'Remove file markers: "【n:n†source】".',
                'Remove any directs to other sources.',
                'Remove any directs to messangers like telegram or whatsapp.'
            ]
            prompt = '\n'.join([
                f"{i+1}. {rule}"
                for i, rule in enumerate(rules)
            ])

        return GPT_REVIEW_MESSAGE.format(
            target=message.text,
            prompt=prompt
        )


class CleanAgent(BaseAgent):
    name: str = "cleaner"
    is_one_shot: bool = True

    async def is_generate(self, message: Message):
        return message.source == "gmail"

    async def get_prompt_new_dialog(self, message: Message):
        return message.text
