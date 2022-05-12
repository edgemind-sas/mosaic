
from pandas import Timestamp
import pandas as pd
from pydantic import BaseModel, Field

from ..config.indicator_config import IndicatorSourceConfig
from .indicator_message import IndicatorMessage


class IndicatorSource(BaseModel):

    name: str = Field(None)
    collection: str = Field(None)
    config: IndicatorSourceConfig = Field(None)
    period: Timestamp = Field(None)

    def __init__(self, name: str, config: IndicatorSourceConfig):

        super().__init__()

        self.name = name
        self.config = config
        self.collection = config.collection
        period_string = config.tags.get("period")
        self.period = pd.to_timedelta(period_string)

    def accept(self, message: IndicatorMessage):

        if self.config.name != message.measurement:
            return False

        for key in self.config.tags.keys():
            if key not in message.tags.keys():
                return False
            if self.config.tags.get(key) != message.tags.get(key):
                return False

        return True

    def dataframe_size(self):
        return 1 + self.config.history_bw + self.config.history_fw
