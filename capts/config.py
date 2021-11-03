import os
from enum import Enum

from capts.businesslogic.task import TaskTracker
from capts.storage import RedisStorage

REDIS_URL = os.environ.get("REDIS_URL")
RABBIT_URL = os.environ.get("RABBIT_URL")

task_tracker = TaskTracker.from_url(REDIS_URL)
redis_storage = RedisStorage(dsn=REDIS_URL)


class CaptchaType(str, Enum):
    fns = "fns"
    alcolicenziat = "alcolicenziat"
