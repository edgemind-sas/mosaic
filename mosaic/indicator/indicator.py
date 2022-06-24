import logging
from pydantic import BaseModel, Field


class Indicator(BaseModel):

    @classmethod
    def from_config(basecls, **config):

        cls_sub_dict = {
            cls.__name__: cls for cls in basecls.__subclasses__()}

        clsname = config.pop("class_name")
        cls = cls_sub_dict.get(clsname)

        if cls is None:
            raise ValueError(
                f"{clsname} is not a subclass of {basecls.__name__}")

        return cls(**config)

    def compute(self, *data):

        logging.error(
            "Generic indicator type doesn't have a compute indicator implementation")
        return {}


class IndicatorOHLCV(Indicator):

    ohlcv_names: dict = Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")
