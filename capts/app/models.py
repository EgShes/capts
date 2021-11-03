from pydantic import BaseModel


class Message(BaseModel):
    task_id: str
    storage_namespace: str


class NeuralNetResult(BaseModel):
    text: str
    confidence: float


class ApiGetResult(BaseModel):
    status: str
    result: NeuralNetResult


class ApiPostResult(BaseModel):
    id: str


class NotFoundResponse(BaseModel):
    detail: str
