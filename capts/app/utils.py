from enum import Enum

from capts.businesslogic.task import TaskStatus


class CaptchaType(str, Enum):
    fns = "fns"
    alcolicenziat = "alcolicenziat"


status2message = {
    TaskStatus.received: "Waiting for processing",
    TaskStatus.processing: "In processing",
    TaskStatus.finished: "Processed",
}
