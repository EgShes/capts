from pydantic import BaseModel


class Message(BaseModel):
    id: str
    storage_namespace: str
