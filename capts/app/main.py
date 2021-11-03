from io import BytesIO

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

from capts.app.models import (
    ApiGetResult,
    ApiPostResult,
    Message,
    NeuralNetResult,
    NotFoundResponse,
)
from capts.app.utils import status2message
from capts.businesslogic.queue import Config, MessagePublisher, get_publisher_channel
from capts.businesslogic.task import Task, TaskNotRegisteredError
from capts.config import CaptchaType, api_logger, redis_storage, task_tracker

publisher_channel = get_publisher_channel()
api_logger.info(f"Connected to channel {publisher_channel}")

captcha2publisher = {
    CaptchaType.fns: MessagePublisher(publisher_channel, Config.EXCHANGE, Config.FNS_QUEUE_ROUTING_KEY),
    CaptchaType.alcolicenziat: MessagePublisher(publisher_channel, Config.EXCHANGE, Config.ALCO_QUEUE_ROUTING_KEY),
}


app = FastAPI()


def load_image_into_numpy_array(data):
    return np.array(Image.open(BytesIO(data)))


@app.post("/process_captcha/", response_model=ApiPostResult)
async def process_image(captcha_type: CaptchaType, captcha: UploadFile = File(...)):
    """
    Post one captcha image. You will get an _id_. Use this id to check for result

    __fns__ captcha [example](https://disk.yandex.ru/i/fefdsNdRlD9jWQ)

    __alcolicenziat__ captcha [example](https://disk.yandex.ru/i/NjHmMHWj2Au85A)
    """
    captcha = np.array(Image.open(BytesIO(await captcha.read())))
    task = Task()
    task_tracker.register_task(task)
    redis_storage.set_namespace(captcha_type.name)
    redis_storage[task.id] = captcha
    captcha2publisher[captcha_type].publish_message(Message(task_id=task.id, storage_namespace=captcha_type.name))
    return ApiPostResult(id=task.id)


@app.get("/result/", response_model=ApiGetResult, responses={404: {"model": NotFoundResponse}})
async def result(captcha_id: str):
    """
    Get result for the image you posted.

    Sent captcha can have 4 statuses:
    - "Waiting for processing" (awaits for neural net to free)
    - "In processing" (neural net is predicting)
    - "Processed" (captcha is solved and you can use the result)
    - "Failed to process" (some internal server error has happened)
    """
    try:
        task = task_tracker.get_task(captcha_id)
    except TaskNotRegisteredError:
        raise HTTPException(status_code=404, detail=f"Task {captcha_id} not found")
    return ApiGetResult(
        status=status2message[task.status],
        result=NeuralNetResult(text=task.result.text, confidence=task.result.confidence),
    )
