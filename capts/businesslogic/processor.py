import abc
from typing import List

import numpy as np
import torch
from pika import BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from pika.amqp_object import Method
from torch.nn import Module

from capts.app.models import Message
from capts.businesslogic.task import Result, TaskStatus
from capts.businesslogic.utils import norm_image
from capts.config import redis_storage, task_tracker


class ExpectedException(Exception):
    pass


def handle_unhandled_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception:
            _, channel, method, _, body = args
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            message = Message.parse_raw(body)
            task_tracker.update_status(message.task_id, status=TaskStatus.failed)
            return
        return result

    return wrapper


class Processor(abc.ABC):
    def __init__(self, model: Module, channel: BlockingChannel, in_queue: str):
        self.model = model
        self.channel = channel
        self.channel.basic_consume(queue=in_queue, on_message_callback=self._handle_request)
        self.channel.basic_qos(prefetch_count=1)

    def process(self, captcha: np.ndarray) -> Result:
        inputs = self.preprocess(captcha)
        net_output = self.predict(inputs)
        result = self.postprocess(net_output)
        return result

    @torch.no_grad()
    def predict(self, captchas: List[torch.Tensor]):
        return self.model(captchas)

    @abc.abstractmethod
    def preprocess(self, image: np.ndarray) -> List[torch.Tensor]:
        """Preprocess captcha to put into model"""

    @abc.abstractmethod
    def postprocess(self, prediction) -> Result:
        """Postprocess net output"""

    @handle_unhandled_exceptions
    def _handle_request(self, channel: BlockingChannel, method: Method, properties: BasicProperties, body: bytes):
        message = Message.parse_raw(body)
        task_tracker.update_status(message.task_id, status=TaskStatus.processing)

        redis_storage.set_namespace(message.storage_namespace)
        try:
            image = redis_storage.pop(message.task_id)
        except KeyError as e:
            raise ExpectedException(f"Image with key {message.task_id} not found") from e

        result = self.process(image)
        task_tracker.publish_result(message.task_id, result)
        task_tracker.update_status(message.task_id, status=TaskStatus.finished)

        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start_consuming(self):
        self.channel.start_consuming()


class FnsCaptchaProcessor(Processor):
    def preprocess(self, image: np.ndarray) -> List[torch.Tensor]:
        image = image[:, :, :3]
        return [torch.from_numpy(image / 255.0).permute(2, 0, 1).float()]

    def postprocess(self, prediction) -> Result:
        pred_class = [self.model.vocab[i] for i in list(prediction[0]["labels"].detach().cpu().numpy())]
        pred_boxes = [[(i[0], i[1]), (i[2], i[3])] for i in list(prediction[0]["boxes"].detach().cpu().numpy())]
        pred_score = prediction[0]["scores"].detach().cpu().numpy()

        # keep = pred_score > self.threshold
        keep = pred_score > 0.9
        pred_class, pred_boxes, pred_score = (
            np.array(pred_class)[keep],
            np.array(pred_boxes)[keep],
            pred_score[keep],
        )

        indxs = np.argsort([i[0][0] for i in pred_boxes])
        result = Result(captcha_text="".join(np.array(pred_class)[indxs]), confidence=float(np.prod(pred_score)))
        return result


class AlcoCaptchaProcessor(Processor):
    def preprocess(self, image: np.ndarray) -> List[torch.Tensor]:
        image = image[:, :, :3]
        image = norm_image(image)
        return [torch.from_numpy(image).permute(2, 0, 1).float()]

    def postprocess(self, prediction) -> Result:
        pred_class = [self.model.vocab[i] for i in list(prediction[0]["labels"].detach().cpu().numpy())]
        pred_boxes = [[(i[0], i[1]), (i[2], i[3])] for i in list(prediction[0]["boxes"].detach().cpu().numpy())]
        pred_score = prediction[0]["scores"].detach().cpu().numpy()

        keep = pred_score > 0.9
        pred_class, pred_boxes, pred_score = (
            np.array(pred_class)[keep],
            np.array(pred_boxes)[keep],
            pred_score[keep],
        )

        indxs = np.argsort([i[0][0] for i in pred_boxes])
        result = Result(captcha_text="".join(np.array(pred_class)[indxs]), confidence=float(np.prod(pred_score)))
        return result
