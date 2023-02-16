import pandas as pd
from pydantic import BaseModel, Field
from ..utils import lag as lagfun
import warnings


class Indicator(BaseModel):

    lag: int = Field(0, description="Use `offset` attribute of compute method instead")

    offset: int = Field(0, description="Use to return indic_(t - offset)")

    offset_fmt: str = Field("{indic_name}[{offset}]",
                            description="Offset format for columns naming")
    
    @property
    def bw_window(self):
        return self.offset

    @property
    def fw_window(self):
        return 0

    @classmethod
    def get_subclasses(cls, recursive=True):
        """ Enumerates all subclasses of a given class.

        # Arguments
        cls: class. The class to enumerate subclasses for.
        recursive: bool (default: True). If True, recursively finds all sub-classes.

        # Return value
        A list of subclasses of `cls`.
        """
        sub = cls.__subclasses__()
        if recursive:
            for cls in sub:
                sub.extend(cls.get_subclasses(recursive))
        return sub

    @classmethod
    def from_config(basecls, **config):

        cls_sub_dict = {
            cls.__name__: cls for cls in Indicator.get_subclasses(basecls)}

        clsname = config.pop("class_name")
        cls = cls_sub_dict.get(clsname)

        if cls is None:
            raise ValueError(
                f"{clsname} is not a subclass of {basecls.__name__}")

        return cls(**config)

    def apply_lag(self, indic, lag=None):

        warnings.warn("apply_lag is deprecated use apply_offset instead",
                      DeprecationWarning)

        lag_to_apply = lag if not(lag is None) else self.lag
            
        return lagfun(indic, lag_to_apply) if lag_to_apply != 0 else indic

    def apply_offset(self, indic):

        indic_offset = indic.shift(self.offset)
        if isinstance(indic_offset, pd.DataFrame):
            indic_offset.columns = [self.offset_fmt.format(
                indic_name=col, offset=-self.offset) for col in indic_offset.columns]
        else:
            indic_offset.name = \
                self.offset_fmt.format(
                    indic_name=indic_offset.name,
                    offset=-self.offset)

        return indic_offset
    
    def compute(self, *data, offset=None, **kwrds):

        if not (offset is None):
            self.offset = offset

        # raise NotImplementedError(
        #     "Generic indicator type doesn't have a compute indicator implementation")


class IndicatorOHLCV(Indicator):

    ohlcv_names: dict = Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")
