
from typing import Type

import asyncio
import aioimaplib
import aiosmtplib
import aiohttp

import email
import email.utils
import email.policy
from email.mime.text import MIMEText
from email.header import Header

from datetime import datetime
from babel.dates import format_datetime, Locale

from bs4 import BeautifulSoup

from utils import string_to_uuid

from dtypes.message import Message
from dtypes.message.statuses import WaitingForReviewStatus
from dtypes.user import BaseUser
from dtypes.source_type import GmailSourceType
from dtypes.dialog import Dialog

from config import IMAP_SSL_HOST, IMAP_SSL_PORT
from config import SMTP_SSL_HOST, SMTP_SSL_PORT
from config import GMAIL_USERNAME, GMAIL_PASSWORD
from config import GMAIL_DELAY, DATABASE_CHECK_DELAY
from config import EMAIL_KEYS_TO_FIELDS
from config import GMAIL_EN_MESSAGE, GMAIL_REVIEW
from config import GMAIL_FORM
from config import API

from utils import clear

from . import BaseSourceListener, ListenerOutput


CONN_API = API["conn"]["entry"]
PUB_API = API["pub"]["entry"]


def get_text_from_reply(html):
    soup = BeautifulSoup(html, "html.parser")

    blacklist = {
        "name": ["12345message", "12345message_block"],
        "style": ["margin:0px 0px 0px 0.8ex;border-left:1px solid rgb(0, 0, 0)"]
    }

    for rule in blacklist:
        rule_blacklist = blacklist[rule]

        for subrule in rule_blacklist:

            for match in soup.select(f"[{rule}*='{subrule}']"):
                match.decompose()

    return soup.get_text()


class GmailSourceListener(BaseSourceListener):
    source_type = GmailSourceType()
    client: aioimaplib.IMAP4_SSL
    outcoming_delay = DATABASE_CHECK_DELAY
    incoming_delay = GMAIL_DELAY
    smtp_client: aiosmtplib.SMTP

    def __init__(self, *args, **kwargs):
        BaseSourceListener.__init__(self, *args, **kwargs)
        self.idle = None

    async def handle_message(self, message_id, raw_message) -> ListenerOutput:
        message = email.message_from_bytes(raw_message)

        text_plain = None
        text_html = None

        for part in message.walk():
            if part.get_content_type() == 'text/plain' and text_plain is None:
                text_plain = part.get_payload(decode=True).decode()

            if part.get_content_type() == 'text/html' and text_html is None:
                text_html = part.get_payload(decode=True).decode()

        http = aiohttp.ClientSession(loop=asyncio.get_running_loop())

        async with http.get(f"{CONN_API}/config", json={"id": "main"}) as response:
            config_response = await response.json()

        reviewers = list(map(lambda x: x["id"], config_response["data"]["reviewers"]))
        sender = email.utils.parseaddr(message.get('From'))[1]
        sender_id = string_to_uuid(sender)

        soup = BeautifulSoup(text_html, "html.parser")
        body = get_text_from_reply(text_html)

        if sender_id in reviewers:
            ask_message_id = soup.select_one("span[name='client_message_id']").get_text(strip=True)
            reply_message_id = soup.select_one("span[name='bot_message_id']").get_text(strip=True)
            recipient_id = soup.select_one("span[name='client_id']").get_text(strip=True)

            if None in (ask_message_id, recipient_id):
                await http.close()
                return self.log.warning(f"Cant find reply_to creds -> {reply_message_id} -> {recipient_id}")

            message = Message(**{
                "id": '_'.join((ask_message_id, "review", sender_id)),
                "reply_to_id": reply_message_id,
                "dialog_id": recipient_id,
                "sender_id": sender_id,
                "source": str(self.source_type),
                "status": str(WaitingForReviewStatus()),
                "text": str(body)
            })

            message_data = message.to_dict()

            self.log.debug(f"Trying to add review message -> {message_data}")
            async with http.post(f"{CONN_API}/message", json=clear(message_data)) as response:
                message_response = await response.json()

            self.log.info(f"Got response from adding review message -> {message_response}")
            await http.close()

            return None

        rows = soup.select("td.row")
        data = {}

        for row in rows:
            field = EMAIL_KEYS_TO_FIELDS.get(row["name"])

            if not field:
                continue

            data.update({
                field: row.get_text(strip=True)
            })

        if not data.get('link'):
            self.log.warning(f"Email have wrong type cant find link -> {data}")
            data["link"] = email.utils.parseaddr(message["From"])[1]

            data["text"] = str(body)
            self.log.debug(f"Set link in raw format from email -> {data}")

        subject = data.get("subject")

        if not subject:
            subject = data.get("source_name")

        if not subject:
            try:
                header = email.header.decode_header(message["Subject"])[0]
                subject, encoder = header
                subject = subject.decode(encoder)

            except Exception as err:
                self.log.warning(f"Cant get subject: {err}")

        if not data.get("text"):
            data["text"] = subject if subject else ""

        await http.close()
        return ListenerOutput(
            message_id=str(message_id),
            text=data.get("text"),
            link=data.get("link"),
            firstname=data.get("firstname"),
            phone=data.get("phone"),
            id=string_to_uuid(data.get("link")),
            subject=subject,
            source_link=data.get("source_link")
        )

    async def _connect(self):
        await self.connect_imap()
        await self.connect_smtp()

    async def connect_imap(self):
        while True:
            try:
                self.client = aioimaplib.IMAP4_SSL(host=IMAP_SSL_HOST, port=IMAP_SSL_PORT)
                await self.client.wait_hello_from_server()
                await self.client.login(GMAIL_USERNAME, GMAIL_PASSWORD)

                self.log.info(f"Connected to imap")
                return

            except Exception as err:
                self.log.exception(err)
                self.log.critical(f"Cant connect to imap, trying to reconnect after 10 seconds")
                await asyncio.sleep(10)

    async def connect_smtp(self):
        while True:
            try:
                self.smtp_client = aiosmtplib.SMTP(hostname=SMTP_SSL_HOST, port=SMTP_SSL_PORT, start_tls=True)
                await self.smtp_client.connect()
                await self.smtp_client.login(GMAIL_USERNAME, GMAIL_PASSWORD)
                self.log.info(f"Connected to smtp")
                return

            except Exception as err:
                self.log.exception(err)
                self.log.critical(f"Cant connect to smtp, trying to reconnect after 10 seconds")
                await asyncio.sleep(10)

    async def delay_incoming(self):
        return await asyncio.sleep(self.incoming_delay)

    async def _get_incoming_messages(self) -> list[ListenerOutput]:
        while True:
            try:
                await self.client.select('INBOX')
                status, data = await self.client.search("UNSEEN")

                if status != "OK":
                    return self.log.warning(f"Got bad status from imap -> {status}")

                self.log.debug(f"Got data from imap -> {data}")

                message_ids = data[0].split()

                messages = []
                for message_id in message_ids:
                    message_id = message_id.decode()

                    self.log.info(f"Got new message -> {message_id}")

                    message_bytes = (await self.client.fetch(message_id, "(RFC822)")).lines[1]
                    message = await self.handle_message(message_id, message_bytes)

                    if message:
                        messages.append(message)

                return messages

            except Exception as err:
                await self.connect_imap()
                self.log.exception(err)

    async def send_until_success(self, reciepient, string):
        while True:
            try:
                return await self.smtp_client.sendmail(GMAIL_USERNAME, reciepient, string)

            except aiosmtplib.errors.SMTPConnectError:
                self.log.warning(f"Reconnecting to smtp -> {aiosmtplib.SMTPConnectError}")
                await self.connect_smtp()

            except aiosmtplib.SMTPServerDisconnected:
                self.log.warning(f"Reconnecting to smtp -> {aiosmtplib.SMTPServerDisconnected}")
                await self.connect_smtp()

            except Exception as err:
                self.log.exception(err)
                await self.connect_smtp()

    async def _send_review_message(self, reciepient: Type[BaseUser], client: Type[BaseUser], message: Message, ask_message: Message, dialog: Dialog):
        bot_message_id = '_'.join((message.reply_to_id, "reply"))
        body = GMAIL_REVIEW.format(
            **client.to_dict(),
            client_message_id=ask_message.id,
            bot_message_id=bot_message_id,
            source_link=ask_message.source_link if ask_message.source_link else "UNDETERMINATED",
            subject=ask_message.subject,
            text=ask_message.text,
            gpt_text=message.text,
            send_link=f'{PUB_API}/send/{bot_message_id}'
        )

        msg = MIMEText(body, 'html', 'utf-8')
        msg['Subject'] = Header(f"GPT-review: {client.link.split('/')[-1]}", 'utf-8')
        msg['From'] = GMAIL_USERNAME
        msg['To'] = reciepient.link

        return await self.send_until_success(reciepient.link, msg.as_string())

    async def _send_message(self, reciepient: Type[BaseUser], message: Message, ask_message: Message, dialog: Dialog):
        http = aiohttp.ClientSession(loop=asyncio.get_running_loop())
        history = []

        async with http.get(f"{CONN_API}/dialog/messages", json={
            "id": dialog.id
        }) as response:
            data = await response.json()

            for i in data["data"]:
                if not i["reply_to_id"]:
                    history.append(i)

                elif i["id"].endswith("_reply"):
                    history.append(i)

        async with http.get(f"{CONN_API}/user", json={
            "id": dialog.id
        }) as response:
            data = await response.json()

            client = data["user"]

        await http.close()

        body = "<div name='12345message'>\n"

        body += GMAIL_EN_MESSAGE.format(
            text=message.text.replace("<p>", "").replace("</p>", "")+"\n<br>\n",
            firstname=dialog.gpt_face["firstname"],
            lastname=dialog.gpt_face["lastname"]
        )

        for i, msg in enumerate(history[-2::-1]):

            f = "EEE, d MMM yyyy 'г.' 'в' HH:mm"
            locale = Locale("ru")
            date = f"{format_datetime(datetime.fromtimestamp(msg['date']), format=f, locale=locale)} " if msg.get("date") else ""

            if not msg['reply_to_id']:
                client_name = f"{client['firstname']} " if client['firstname'] else ""

                if str(dialog.source) == "gmail":
                    client_link = f"<a href='mailto:{client['link']}'>{client['link']}</a>"

                elif str(dialog.source) == "telegram":
                    client_link = f"<a href='https://t.me/{client['link']}'>{client['link']}</a>"

                elif str(dialog.source) == "whatsapp":
                    client_link = f"<a href='https://wa.me/{client['link']}'>{client['link']}</a>"

            else:
                client_name = "Oleg Shevchenko "

                if str(dialog.source) == "gmail":
                    client_link = "<a href='mailto:manager.innovacg@gmail.com'>manager.innovacg@gmail.com</a>"

                elif str(dialog.source) == "telegram":
                    client_link = f"<a href='https://t.me/innovasupport'>innovasupport</a>"

                elif str(dialog.source) == "whatsapp":
                    client_link = f"<a href='https://wa.me/380507122670'>innovasupport</a>"

            meta = f"{date}{client_name}<{client_link}>:"

            body += '\n'.join((
                "<br>",
                meta,
                "<br>",
                '<blockquote class="gmail_quote" name="12345message_block" style="margin:0px 0px 0px 0.8ex;border-left:1px solid rgb(201, 202, 205);padding-left:1ex">',
            ))

            if i == len(history) - 2 and str(dialog.source) == "gmail":
                body += "\n".join((
                    GMAIL_FORM.format(
                        firstname=client['firstname'],
                        phone=client['phone'],
                        link=client['link'],
                        source_link=msg['source_link'],
                        text=msg['text']
                    ),
                    "<br>"
                ))

            elif msg["id"].endswith("_reply"):
                body += GMAIL_EN_MESSAGE.format(
                    text=msg["text"].replace("<p>", "").replace("</p>", "") + "\n<br>\n",
                    firstname=dialog.gpt_face["firstname"],
                    lastname=dialog.gpt_face["lastname"]
                )

            else:
                body += "\n".join((
                     msg["text"].replace("<p>", "").replace("</p>", ""),
                     "<br>"
                 ))

        for _ in history:
            body += "\n</blockquote>"

        body += "\n</div>"

        resp = MIMEText(body, 'html', 'utf-8')
        resp['Subject'] = Header(''.join((
            f"{msg['source_link'].replace('https://', '').split('/')[0]}: " if msg.get("source_link") else "",
            f"запрос по {msg['subject']} " if msg.get("subject") else "",
        )))

        try:
            message_bytes = (await self.client.fetch(message.reply_to_id.split("_")[-1], "(RFC822)")).lines[1]
            message_raw = email.message_from_bytes(message_bytes)
            message_id = message_raw.get("Message-ID")
            resp["In-Reply-To"] = message_id

        except Exception as err:
            self.log.warning(f"Cant find reply to message id -> {message}")

        resp['From'] = f"Oleg Shevchenko <{GMAIL_USERNAME}>"
        resp['To'] = reciepient.link

        return await self.send_until_success(reciepient.link, resp.as_string())
