from typing import Any, Dict
from pydantic import BaseModel, Field
from pandas import Timestamp
import pandas as pd


class IndicatorMessage(BaseModel):
    measurement: str = Field(None)
    time: Timestamp = Field(None)
    tags: Dict[str, str] = Field({})
    fields: Dict[str, Any] = Field({})

    def __init__(self, **data):
        super().__init__(**data)

    def escape_strings(self, field):
        value = self.fields.get(field)
        if isinstance(value, str):
            return f'"{value}"'
        else:
            return value

    def to_line_protocol(self):

        tags = ",".join(
            f'{tag}={self.tags.get(tag)}' for tag in self.tags.keys())
        fields = ",".join(
            f'{field}={self.escape_strings(field)}' for field in self.fields.keys())

        return f'{self.measurement},{tags} {fields} {self.time.value}'

    @classmethod
    def from_line_protocol(basecls, line_protocol_str: str):

        struct = {}

        struct["measurement"] = line_protocol_str.partition(",")[0]

        timestamp = int(line_protocol_str.rpartition(" ")[2])
        struct["time"] = pd.to_datetime(timestamp, utc=True, unit='ns')

        tags = {}
        for tag in line_protocol_str.split(" ")[0].partition(",")[2].split(","):
            tags.update({tag.split("=")[0]: tag.split("=")[1]})
        struct["tags"] = tags

        fields = {}
        for field in line_protocol_str.split(" ")[1].split(","):
            fields.update({field.split("=")[0]: field.split("=")[1]})

        struct["fields"] = fields

        return basecls(**struct)
