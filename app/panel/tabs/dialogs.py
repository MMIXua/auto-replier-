
import threading
import operator
import time
from datetime import datetime
import flet as ft
import typing
import requests

from config import API
from dtypes.user import BaseUser, to_user
from utils.utils import generate_gradient


CONN_API = API["conn"]["entry"]


class DialogItem(ft.ElevatedButton):
    def __init__(self, dialog: typing.Type[BaseUser], bgcolor, callback=lambda x: x):
        self.dialog = dialog
        self.callback = callback

        ft.ElevatedButton.__init__(self, on_click=self.on_callback)

        self.style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(
                radius=5
            ),
            padding=ft.Padding(
                left=10,
                right=10,
                top=10,
                bottom=10
            ),
            bgcolor=bgcolor
        )

        self.content = self.get_content()

    def on_callback(self, e):
        self.callback(self.dialog)

    def get_content(self):
        data = []

        for x in [self.dialog.firstname, self.dialog.phone, self.dialog.link, self.dialog.type]:
            if not x:
                continue

            data.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(x, color=ft.colors.WHITE, text_align=ft.TextAlign.LEFT)
                        ]
                    ),
                    expand=True,
                )
            )

        return ft.Column(
            controls=[
                ft.Container(height=10),
                ft.Row(
                    controls=[
                        ft.Text(self.dialog.firstname, color=ft.colors.WHITE)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(height=5),
                ft.Row(
                    controls=[
                        ft.Text(self.dialog.link, color=ft.colors.WHITE)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Row(),
                    expand=True
                ),
                ft.Row(
                    controls=[
                        ft.Text(datetime.fromtimestamp(self.dialog.last_message), color=ft.colors.WHITE)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(height=10)
            ],
            spacing=0,
            horizontal_alignment=ft.MainAxisAlignment.START
        )


class DialogsList(ft.Container):
    def __init__(self, callback=lambda x: x):
        ft.Container.__init__(self)

        self.callback = callback
        self.dialogs: list[typing.Type[BaseUser]] = []

        self.expand = True
        self.content = self.get_content()

        self.load_dialogs()
        self.thread = threading.Thread(target=self.dialog_loader)
        self.thread.start()

    def load_dialogs(self):
        response = requests.get(f"{CONN_API}/users", json={})
        data = response.json()

        self.dialogs = list(map(lambda x: to_user(x), data["data"]))
        self.dialogs.sort(key=operator.attrgetter('last_message'), reverse=True)

        gradient = generate_gradient((128, 128, 128), (0, 0, 0), len(self.dialogs))

        dialog_items = []
        day_dialog_items = []
        first_day_dialog = self.dialogs[0]

        for i, dialog in enumerate(self.dialogs):
            if dialog.type == "reviewer":
                continue

            if first_day_dialog.last_message - dialog.last_message > 43200:
                dialog_items += [
                    ft.Container(
                        ft.Row(
                            controls=[
                                ft.Text(datetime.fromtimestamp(first_day_dialog.last_message).strftime("%A, %m.%d.%Y")),
                            ],
                            expand=True,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        height=50,
                        bgcolor="#363636",
                        border_radius=5
                    ),
                    ft.GridView(
                        controls=day_dialog_items,
                        spacing=5,
                        run_spacing=5,
                        max_extent=300,
                        child_aspect_ratio=1.0
                    ),
                    ft.Container(height=10)
                ]

                first_day_dialog = dialog
                day_dialog_items = []

            day_dialog_items.append(DialogItem(dialog, gradient[i], self.callback))

        self.content.controls = dialog_items

    def dialog_loader(self):
        while True:
            time.sleep(10)
            self.load_dialogs()

    def get_content(self):
        return ft.Column(
            controls=[],
            expand=True,
            scroll=True
        )


class DialogsTab(ft.Tab):
    def __init__(self, controller):
        ft.Tab.__init__(self)

        self.controller = controller
        self.text = "dialogs"

        self.content = self.get_content()

    def open_dialog(self, dialog):
        self.controller.open_dialog(dialog)
        self.page.update()

    def get_content(self):
        return ft.Row(
            controls=[
                DialogsList(self.open_dialog),
            ],
            expand=True
        )
