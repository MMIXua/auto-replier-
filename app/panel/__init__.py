import threading
import time

import flet as ft

from .tabs import DialogsTab, ChatTab


class MainApp(ft.Tabs):
    def __init__(self):
        ft.Tabs.__init__(self)

        self.page = None
        self.expand = True
        self.selected_index = 0
        self.divider_height = 0
        self.indicator_color = ft.colors.TRANSPARENT
        self.animation_duration = 300

        self.dialogs_tab = DialogsTab(self)

        self.tabs = [self.dialogs_tab]

        self.thread = threading.Thread(target=self.updater)
        self.thread.start()

    def updater(self):
        while True:
            if self.page:
                self.page.update()

            time.sleep(10)

    def open_dialog(self, dialog):
        chat = ChatTab(self, dialog)
        self.selected_index = 1
        self.tabs = [self.tabs[0], chat, *self.tabs[1:]]

    def __run(self, page):
        self.page = page
        self.page.add(self)

    def run(self):
        return ft.app(target=self.__run)
