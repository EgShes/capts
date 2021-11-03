from pydantic import BaseModel


class Message(BaseModel):
    task_id: str
    storage_namespace: str
