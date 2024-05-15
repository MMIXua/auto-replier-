
import sys
from os import path


IS_DEBUG = True


# logger
LOG_LEVEL = "DEBUG"

# db
MONGODB_URI = "mongodb+srv://root:nTYsua2bWYlTyUlI@autoreplies.wsytfu4.mongodb.net/?retryWrites=true&w=majority&appName=AutoReplies"

# gpt
GPT_API_KEY = "API"
GPT_ASSISTANT_ID = "asst_cQzJEk99zoDwdJWNahXs9bOd"
GPT_TIMEOUT = 120
GPT_ASK_MESSAGE = """
YOUR_NAME: {bot_firstname} {bot_lastname}
YOUR_AGE: {bot_age}
YOUR_SEX: {bot_sex}
CLIENT_NAME: {client_name}
SUBJECT: {subject}
ASK: {ask}
"""
GPT_REVIEW_MESSAGE = """
TO_REVIEW: {target}
CORRECTION: {prompt}
"""

# message_handler
MESSAGE_HANDLER_DELAY = 5


# source_listeners (seconds)
DATABASE_CHECK_DELAY = 5
GMAIL_DELAY = 5


# updater
UPDATER_DELAY = 10


# api
API = {
    "conn": {
        "host": "127.0.0.1",
        "port": 6660,
        "entry": "http://127.0.0.1:6660"
    },
    "pub": {
        "host": "127.0.0.1",
        "port": 6661,
        "entry": "https://ai.innovaltd.click"
    },
    "wp": {
        "host": "127.0.0.1",
        "port": 6662,
        "entry": "http://127.0.0.1:6662"
    }
}


# gmail
IMAP_SSL_HOST = 'imap.gmail.com'
IMAP_SSL_PORT = 993

SMTP_SSL_HOST = 'smtp.gmail.com'
SMTP_SSL_PORT = 587

GMAIL_USERNAME = "manager.innovacg@gmail.com"
GMAIL_PASSWORD = "mczr dssz powr efdk"

FIELDS = ["firstname", "link", "phone", "text"]
EMAIL_KEYS_TO_FIELDS = {
    "name": "firstname",
    "mail": "link",
    "message": "text",
    "phone": "phone",
    "page_link": "source_link",
    "subject": "subject",
    "page": "source_name"
}

GMAIL_REVIEW = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            color: #333;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .client-data, .client-message, .gpt-answer, .meta-data {{
            margin-bottom: 10px;
        }}
        .title {{
            color: #0056b3;
            font-weight: bold;
        }}
        .info-block {{
            margin: 10px 0;
        }}
        .value {{
          font-family: bold;
        }}
        .green-button {{
            width: 100%;
            background-color: green;
            padding: 10px 0;
            text-align: center;
            text-decoration: none;
            display: block;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
        }}
    </style>
</head>
<body>

<div name="12345message">

<div class="container meta-data">
    <div class="title">Meta Data</div>
    <div class="info-block">Client ID: <span class="value" name='client_id'>{id}</span></div>
    <div class="info-block">Client Message ID: <span class="value" name='client_message_id'>{client_message_id}</span></div>
    <div class="info-block">Bot Message ID: <span class="value" name='bot_message_id'>{bot_message_id}</span></div>
</div>

<div class="container client-data">
    <div class="title">Client Data</div>
    <div class="info-block">Client Name: <span class="value">{firstname}</span></div>
    <div class="info-block">Phone: <span class="value">{phone}</span></div>
    <div class="info-block">Subject: <span class="value">{subject}</span></div>
    <div class="info-block">Source: <span class="value">{source}</span></div>
    <div class="info-block">Source Link: <a href="{source_link}">{source_link}</a></div>
    <div class="info-block">Client Link: <a href="{link}">{link}</a></div>
</div>

<div class="container client-message">
    <div class="title">Client Message</div>
    <p>{text}</p>
</div>

<div class="container gpt-answer">
    <div class="title">GPT Answer</div>
    <p>{gpt_text}</p>
</div>
<a href="{send_link}" class="green-button" style="color: white">Send</a>

</div>
</body>
</html>
"""

GMAIL_EN_MESSAGE = """{text}<br>
Have a nice day!<br>
_____________________________________________________________________________________<br>
Kind regards, {firstname} {lastname}, Chief Development Officer of<br>
the Group of Companies "INNOVA Consulting Group"<br>
mob.: +38 067-77-77-230 (Telegram, WhatsApp, Viber)<br>
_____________________________________________________________________________________<br>
INNOVA Consulting Group (innova.ua) - approved by 11-years of experience services for business:<br>
<a href='https://legal.ua'>www.Legal.ua</a>  => approved legal solutions for SME<br>
<a href='https://keys.ua'>www.Keys.ua</a> => audit and accounting services<br>
<a href='https://mmix.ua'>www.Mmix.ua</a>  => marketing services, web-sites development<br>
<a href='https://crystal.tax'>www.Crystal.tax</a>  => international tax planning<br>
"""

GMAIL_FORM = """Это сообщение было отправлено пользователем: <b>{firstname}</b>, с сайта <a href="{source_link}">{source_link}</a><br><br>
<b>Имя</b>: {firstname}<br>
<b>Email</b>: {link}<br>
<b>Телефон</b>: {phone}<br>
<b>Сообщение</b>: {text}<br>
<b>Ссылка на страницу</b>:	<a href="{source_link}">{source_link}</a>
"""


# telegram
TELEGRAM_SESSION_NAME = "380671021317.session"

TELEGRAM_REVIEW = ["""
<b>Meta Data</b>
-------------------
Client ID: <div name="id">{id}</div>
Client Message ID: {client_message_id}
Bot Message ID: {bot_message_id}

<b>Client Data</b>
-------------------
Client Name: {firstname}
Phone: {phone}</span></div>
Subject: {subject}
Source: {source}
Source Link: <a href="{source_link}">{source_link}</a>
Client Link: <a href="{link}">{link}</a>

<b> Client Message</b>
-------------------
{text}

<b> GPT Answer</b>
-------------------
{gpt_text}
"""]

"""
<a href='{send_link}'>Send Message</a>
"""


# whatsapp
WHATSAPP_TOKEN = "EAADyZBFUTF2wBOZCu390Vcv5L9cZC1v69ZBOz89BCw1nOT1xleinUHE8UMAKMUiMPCFQygdRJngZBSWDRrnhHJH3990ty1fwj1NkWbG7AqgMrdZBV3Oe47SPq8a6yxyOU0WpWh5uldlZBvgc5oBbo9IiahzDiOZCW2vvMUU2IZASV360BLvvbxYQivUlYwvZAwgz7Q"
WHATSAPP_PHONE = 279412821923939


# google sheets
SHEET_ID = "1Ucrbgp_iQuNYNPF-7pEHUSfF0nZiiFT7v0smucP1ejg"
SHEET_FACES_NAME = "faces"
SHEET_PAYMENTS_NAME = "payments"
SHEET_REVIEWERS_NAME = "reviewers"
SHEET_ASSISTANTS_NAME = "assistants"


# resources
ROOT_DIR = path.dirname(path.abspath(sys.argv[0]))
RESOURCES_DIR = path.join(ROOT_DIR, "resources")
STATIC_DIR = path.join(RESOURCES_DIR, "static")
LOGS_PATH = path.join(RESOURCES_DIR, "logs", "{module}.log")
TELEGRAM_SESSIONS_PATH = path.join(RESOURCES_DIR, "telegram_sessions")
TELEGRAM_SESSION_PATH = path.join(TELEGRAM_SESSIONS_PATH, TELEGRAM_SESSION_NAME)
GOOGLE_CREDS_PATH = path.join(RESOURCES_DIR, "google")
SHEETS_CREDS_PATH = path.join(GOOGLE_CREDS_PATH, "sheets_creds.json")
HTML_TEMPLATES_PATH = path.join(RESOURCES_DIR, "templates")
