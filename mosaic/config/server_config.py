from typing import Dict, List
from pydantic import BaseModel, Field


class MessageServerConfig(BaseModel):
    host: str = Field(None)
    write_topic: str = Field(None)
    consumer_id: str = Field(None)


class DbServerConfig(BaseModel):
    org: str = Field(None)
    collection: str = Field(None)
    url: str = Field(None)
    token: str = Field(None)


class ServerConfig(BaseModel):
    db: DbServerConfig = Field(None)
    message: MessageServerConfig = Field(None)
