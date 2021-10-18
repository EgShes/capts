from enum import Enum
from uuid import uuid4

from fastapi import FastAPI

from capts.businesslogic.task import Task, TaskNotRegisteredError, TaskStatus
from capts.config import task_tracker


class CaptchaType(str, Enum):
    fns = "fns"
    alcolicenziat = "alcolicenziat"


status2message = {
    TaskStatus.received: 'Waiting for processing',
    TaskStatus.processing: 'In processing',
    TaskStatus.finished: 'Processed'
}


app = FastAPI()


@app.post("/process_captcha/{captcha_type}")
def process_image(captcha_type: CaptchaType):
    task = Task()
    task_tracker.register_task(task)
    return {"id": task.id}


@app.get("/result/{captcha_id}")
def result(captcha_id: str):
    try:
        task = task_tracker.get_task(captcha_id)
    except TaskNotRegisteredError:
        return 404, {'message': f'task {captcha_id} not found'}
    return {"status": status2message[task.status], 'result': task.result}
