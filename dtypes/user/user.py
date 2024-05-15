
from . import BaseUser


class Client(BaseUser):
    type = "client"


class Bot(BaseUser):
    type = "bot"


class Reviwer(BaseUser):
    type = "reviewer"
