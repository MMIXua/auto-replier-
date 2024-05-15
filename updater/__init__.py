
import asyncio
import aiohttp
import pygsheets

from logger import log

from config import UPDATER_DELAY, API
from config import SHEETS_CREDS_PATH, SHEET_ID
from config import SHEET_FACES_NAME, SHEET_PAYMENTS_NAME
from config import SHEET_REVIEWERS_NAME, SHEET_ASSISTANTS_NAME
from utils import string_to_uuid


CONN_API = API["conn"]["entry"]


def to_dict(rows):
    header = rows[0]
    data = []

    for row in rows[1:]:
        data.append({
            header[i]: value for i, value in enumerate(row)
        })

    return data


class Updater:

    def __init__(self):
        self.log = log.bind(classname=self.__class__.__name__)
        self.loop = None

    async def check_sheets(self):
        try:
            gc = pygsheets.authorize(service_file=SHEETS_CREDS_PATH)

        except Exception as err:
            self.log.critical(err)
            exit()

        http = aiohttp.ClientSession(loop=self.loop)

        sheet = gc.open_by_key(SHEET_ID)

        faces = to_dict(sheet.worksheet_by_title(SHEET_FACES_NAME).get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix'))
        payments = to_dict(sheet.worksheet_by_title(SHEET_PAYMENTS_NAME).get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix'))
        reviewers = to_dict(sheet.worksheet_by_title(SHEET_REVIEWERS_NAME).get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix'))
        assistants = to_dict(sheet.worksheet_by_title(SHEET_ASSISTANTS_NAME).get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix'))[0]

        fields = ["source", "id", "link"]
        reviewers_users = []
        for reviewer in reviewers:
            is_skip = False

            for field in fields:
                if field not in reviewer:
                    is_skip = True
                    break

            if is_skip:
                continue

            if reviewer["source"] == "gmail":
                reviewer["id"] = string_to_uuid(reviewer["link"])

            reviewers_users.append(reviewer)
            async with http.post(f"{CONN_API}/user", json={
                "type": "reviewer",
                "id": reviewer["id"],
                "link": reviewer["link"],
                "source": reviewer["source"]
            }) as response:
                user_response = await response.json()

            self.log.debug(f"Got response from adding reviewer -> {user_response}")

        config = {
            "id": "main",
            "data": {
                "faces": faces,
                "payments": payments,
                "reviewers": reviewers_users,
                "assistants": assistants
            }
        }
        self.log.info(f"Got gpt config -> {config}")

        async with http.get(f"{CONN_API}/config", json={
            "id": "main"
        }) as response:
            config_response = await response.json()

        if config_response["data"]:
            self.log.info(f"Config gpt exists so updating it")

            async with http.post(f"{CONN_API}/update_config", json=config) as response:
                update_config_response = await response.json()

            self.log.debug(f"Got update_config_response -> {update_config_response}")

        else:
            self.log.info(f"There is not such config gpt so creating new")

            async with http.post(f"{CONN_API}/config", json=config) as response:
                add_config_response = await response.json()

            self.log.debug(f"Got add_config_response -> {add_config_response}")

        await http.close()

    async def listen_for_updates(self):
        while True:
            try:
                await asyncio.gather(self.check_sheets())

            except Exception as err:
                self.log.exception(err)

            await asyncio.sleep(UPDATER_DELAY)

    def listen(self):
        loop = asyncio.new_event_loop()
        self.loop = loop
        loop.run_until_complete(self.listen_for_updates())
