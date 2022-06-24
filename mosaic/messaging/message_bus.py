
from pydantic import BaseModel, Field


class MessageBus(BaseModel):

    host: str = Field(None)
    write_topic: str = Field(None)
    consumer_id: str = Field(None)
