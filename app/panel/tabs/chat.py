import threading
import time

import flet as ft
import typing
import requests

from markdownify import markdownify as md
from datetime import datetime

from dtypes.user import BaseUser
from dtypes.message import Message
from config import API


CONN_API = API["conn"]["entry"]


spacer = ft.Container(expand=True)


class MessageItem(ft.Container):
    def __init__(self, message):
        self.message: Message = message

        ft.Container.__init__(self)

        self.content = self.get_content()

    def get_content(self):

        text_block = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Markdown(
                        md(self.message.text),
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text(
                                    datetime.fromtimestamp(self.message.date).strftime("%H:%M"),
                                    size=12
                                )
                            ],
                            alignment=ft.MainAxisAlignment.END
                        )
                    )
                ]
            ),
            bgcolor="#242424",
            padding=10,
            expand=True,
            border_radius=10
        )

        if self.message.reply_to_id:
            controls = [spacer, text_block]

        else:
            controls = [text_block, spacer]

        return ft.Row(
            controls=controls,
            spacing=25
        )


class ChatTab(ft.Tab):
    def __init__(self, controller, dialog):
        ft.Tab.__init__(self)

        self.controller = controller

        self.user: typing.Type[BaseUser] = dialog
        self.messages: list[Message] = []

        self.save_file_dialog = ft.FilePicker(on_result=self.save_dialog)
        self.controller.page.overlay.extend([self.save_file_dialog])

        self.text = self.user.firstname

        self.expand = True
        self.messages_box = ft.Column(
            controls=[],
            scroll=True
        )
        self.content = self.get_content()

        self.load_messages()
        self.thread = threading.Thread(target=self.message_loader)
        self.thread.start()

    def save_dialog(self, e: ft.FilePickerResultEvent):
        if not e.path:
            return

        with open(e.path, "w") as f:
            string = ""

            for message in self.messages:
                if message.reply_to_id:
                    string += "MANAGER: "

                else:
                    string += "CLIENT: "

                string += message.text + "\n\n"

            print(string)

            f.write(string)

    def load_messages(self):
        history = []

        response = requests.get(f"{CONN_API}/dialog/messages", json={
            "id": self.user.id
        })

        data = response.json()

        for i in data["data"]:
            if not i["reply_to_id"]:
                history.append(Message(**i))

            elif i["id"].endswith("_reply"):
                history.append(Message(**i))

        new_messages = []
        new_messages_items = []

        first_day_message = None

        for message in history:
            if not first_day_message:
                first_day_message = message
                new_messages_items.append(
                    ft.Container(
                        ft.Row(
                            controls=[
                                spacer,
                                ft.Text(datetime.fromtimestamp(first_day_message.date).strftime("%m.%d.%Y")),
                                spacer
                            ]
                        ),
                        height=75
                    )
                )

            elif message.date - first_day_message.date > 86400:
                first_day_message.date = message.date

                new_messages_items.append(
                    ft.Container(
                        ft.Row(
                            controls=[
                                spacer,
                                ft.Text(datetime.fromtimestamp(first_day_message.date).strftime("%m.%d.%Y")),
                                spacer
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        height=75
                    )
                )

            new_messages.append(message)
            new_messages_items.append(MessageItem(message))

        self.messages = history
        self.messages_box.controls = new_messages_items

    def message_loader(self):
        while True:
            time.sleep(2)
            self.load_messages()

    def get_content(self):
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "chat",
                                icon=ft.icons.SAVE,
                                on_click=lambda _: self.save_file_dialog.save_file(
                                    file_name='.'.join((self.user.id, "txt"))
                                )
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END
                    ),
                    height=50,
                    bgcolor="#242424",
                    border_radius=10
                ),
                ft.Container(
                    content=self.messages_box,
                    expand=True
                )
            ],
            expand=True
        )
