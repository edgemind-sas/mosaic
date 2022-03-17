from typing import Any, Dict
from pydantic import BaseModel, Field
from pandas import Timestamp
import pandas as pd


class IndicatorMessage(BaseModel):
    measurement: str = Field(None)
    time: Timestamp = Field(None)
    tags: Dict[str, str] = Field({})
    fields: Dict[str, Any] = Field({})

    def __init__(self, message: str = None):

        super().__init__()

        if message is not None:
            self.from_line_protocol(message)

    def to_line_protocol(self):

        tags = ",".join(
            f'{tag}={self.tags.get(tag)}' for tag in self.tags.keys())
        fields = ",".join(
            f'{field}={self.fields.get(field)}' for field in self.fields.keys())

        return f'{self.measurement},{tags} {fields} {self.time.value}'

    def from_line_protocol(self, line_protocol_str: str):
        self.measurement = line_protocol_str.partition(",")[0]

        timestamp = int(line_protocol_str.rpartition(" ")[2])
        self.time = pd.to_datetime(timestamp, utc=True, unit='ns')

        for tag in line_protocol_str.split(" ")[0].partition(",")[2].split(","):
            self.tags.update({tag.split("=")[0]: tag.split("=")[1]})

        for field in line_protocol_str.split(" ")[1].split(","):
            self.fields.update({field.split("=")[0]: field.split("=")[1]})
