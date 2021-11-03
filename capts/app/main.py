from io import BytesIO

import numpy as np
from fastapi import FastAPI, File, UploadFile
from PIL import Image

from capts.app.models import Message
from capts.app.utils import status2message
from capts.businesslogic.queue import alco_message_publisher, fns_message_publisher
from capts.businesslogic.task import Task, TaskNotRegisteredError
from capts.config import CaptchaType, redis_storage, task_tracker

captcha2publisher = {
    CaptchaType.fns: fns_message_publisher,
    CaptchaType.alcolicenziat: alco_message_publisher,
}


app = FastAPI()


def load_image_into_numpy_array(data):
    return np.array(Image.open(BytesIO(data)))


@app.post("/process_captcha/")
async def process_image(captcha_type: CaptchaType, captcha: UploadFile = File(...)):
    captcha = np.array(Image.open(BytesIO(await captcha.read())))
    task = Task()
    task_tracker.register_task(task)
    redis_storage.set_namespace(captcha_type.name)
    redis_storage[task.id] = captcha
    captcha2publisher[captcha_type].publish_message(Message(id=task.id, storage_namespace=captcha_type.name))
    return {"id": task.id}


@app.get("/result/")
def result(captcha_id: str):
    try:
        task = task_tracker.get_task(captcha_id)
    except TaskNotRegisteredError:
        return 404, {"message": f"task {captcha_id} not found"}
    return {"status": status2message[task.status], "result": task.result}
