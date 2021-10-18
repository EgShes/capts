import os

from capts.businesslogic.task import TaskTracker

REDIS_URL = os.environ.get("REDIS_URL")
RABBIT_URL = os.environ.get("RABBIT_URL")

task_tracker = TaskTracker.from_url(REDIS_URL)
