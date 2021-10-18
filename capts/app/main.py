from fastapi import FastAPI

from capts.app.models import Message
from capts.app.utils import CaptchaType, status2message
from capts.businesslogic.queue import alco_message_publisher, fns_message_publisher
from capts.businesslogic.task import Task, TaskNotRegisteredError
from capts.config import task_tracker

captcha2publisher = {
    CaptchaType.fns: fns_message_publisher,
    CaptchaType.alcolicenziat: alco_message_publisher,
}


app = FastAPI()


@app.post("/process_captcha/{captcha_type}")
def process_image(captcha_type: CaptchaType):
    task = Task()
    task_tracker.register_task(task)
    captcha2publisher[captcha_type].publish_message(Message(id=task.id, storage_namespace=captcha_type.name))
    return {"id": task.id}


@app.get("/result/{captcha_id}")
def result(captcha_id: str):
    try:
        task = task_tracker.get_task(captcha_id)
    except TaskNotRegisteredError:
        return 404, {"message": f"task {captcha_id} not found"}
    return {"status": status2message[task.status], "result": task.result}
