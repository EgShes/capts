import os
from enum import Enum
from pathlib import Path

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from capts.businesslogic.task import TaskTracker
from capts.businesslogic.utils import Logger
from capts.storage import RedisStorage

api_logger = Logger.from_config("api_logger", Path(__file__).parent / "loggers.conf")
nn_logger = Logger.from_config("nn_logger", Path(__file__).parent / "loggers.conf")
dev_logger = Logger.from_config("development_logger", Path(__file__).parent / "loggers.conf")

REDIS_URL = os.environ.get("REDIS_URL")
REDIS_TTL = int(os.environ.get("REDIS_TTL", 0))
RABBIT_URL = os.environ.get("RABBIT_URL")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT"))
RABBIT_LOGIN = os.environ.get("RABBIT_LOGIN")
RABBIT_PASSWORD = os.environ.get("RABBIT_PASSWORD")
SENTRY_LINK = os.environ.get("SENTRY_LINK")

task_tracker = TaskTracker.from_url(REDIS_URL, ttl=REDIS_TTL)
redis_storage = RedisStorage(dsn=REDIS_URL, ttl=REDIS_TTL)


class CaptchaType(str, Enum):
    fns = "fns"
    alcolicenziat = "alcolicenziat"


sentry_sdk.init(dsn=SENTRY_LINK, integrations=[LoggingIntegration()])
