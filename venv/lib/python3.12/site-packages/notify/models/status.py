from pydantic import BaseModel


class Status(BaseModel):
    status: int
    message: str
    target_type: str
    target: str
