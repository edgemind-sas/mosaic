
from pydantic import BaseModel, Field

from ..config.indicator_config import IndicatorSourceConfig
from .indicator_message import IndicatorMessage


class IndicatorSource(BaseModel):

    name: str = Field(None)
    config: IndicatorSourceConfig = Field(None)

    def __init__(self, name: str, config: IndicatorSourceConfig):

        super().__init__()

        self.name = name
        self.config = config

    def accept(self, message: IndicatorMessage):

        if self.config.id != message.measurement:
            return False

        for key in self.config.tags.keys():
            if key not in message.tags.keys():
                return False
            if self.config.tags.get(key) != message.tags.get(key):
                return False

        return True
