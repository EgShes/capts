import json
import uuid
from enum import Enum, auto
from typing import Optional, Union
from uuid import uuid4

from redis import Redis


class TaskStatus(Enum):
    received = auto()
    processing = auto()
    finished = auto()


class Task:

    def __init__(self, id: Optional[Union[uuid.UUID, str]] = None, status: TaskStatus = TaskStatus.received, result: str = ''):
        self.id = str(uuid4()) if id is None else str(id)
        self.status = status
        self.result = result

    def to_json(self) -> str:
        return json.dumps({'id': self.id, 'status': self.status.value, 'result': self.result})

    @classmethod
    def from_json(cls, json_string: str):
        data = json.loads(json_string)
        data['status'] = TaskStatus(data['status'])
        return cls(**data)


class TaskNotRegisteredError(Exception):
    pass


class RedisNotInitializedError(Exception):
    pass


class TaskTracker:

    def __init__(self, redis: Redis):
        self._redis = redis

    @classmethod
    def from_url(cls, url: str):
        try:
            redis = Redis.from_url(url)
        except ValueError as e:
            raise RedisNotInitializedError(f'Could not initialize redis from url: {url}') from e
        return cls(redis)

    def register_task(self, task: Task):
        self._push_task(task)

    def update_status(self, id_: str, status: TaskStatus):
        task = self.get_task(id_)
        task.status = status
        self._push_task(task)

    def get_status(self, id_: str) -> TaskStatus:
        task = self.get_task(id_)
        return task.status

    def get_task(self, id_: str) -> Task:
        if not self._redis.exists(id_):
            raise TaskNotRegisteredError(f'Missing task with id {id_}')
        return Task.from_json(self._redis.get(id_))

    def _push_task(self, task: Task):
        self._redis.set(task.id, task.to_json())
