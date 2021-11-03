import os
from enum import Enum

from capts.businesslogic.task import TaskTracker
from capts.storage import RedisStorage

REDIS_URL = os.environ.get("REDIS_URL")
RABBIT_URL = os.environ.get("RABBIT_URL")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT"))
RABBIT_LOGIN = os.environ.get("RABBIT_LOGIN")
RABBIT_PASSWORD = os.environ.get("RABBIT_PASSWORD")

task_tracker = TaskTracker.from_url(REDIS_URL)
redis_storage = RedisStorage(dsn=REDIS_URL)


class CaptchaType(str, Enum):
    fns = "fns"
    alcolicenziat = "alcolicenziat"
