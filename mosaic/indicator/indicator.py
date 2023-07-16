import pandas as pd
from pydantic import BaseModel, Field
from ..utils import lag as lagfun
import warnings
from plotly.subplots import make_subplots
import plotly.graph_objects as go


class Indicator(BaseModel):
    """
    Technical indicator base class.

    Note on offset: it is important to use offset >= 1 (1 is ok) to avoid anticipation biais.
    when offset == 0 is used, OHLCV at time t is to compute indicator at time t. 
    But from an operational point of view, indicator value at time t cannot be used to interact with
    market at time t.
    Thus using offset == 1 gives at time t the indicator value at time t-1 so we can use this value
    to make decision at time t.
    """
    names_fmt: dict = Field(
        {}, description="Indicator names format mapping")

    lag: int = Field(0, description="Use `offset` attribute of compute method instead")

    offset: int = Field(0, description="Used to return indic_(t - offset)")

    offset_fmt: str = Field("{name}[{offset}]",
                            description="Offset format for columns naming")

    
    @property
    def bw_length(self):
        return self.offset

    @property
    def fw_length(self):
        return 0

    # @property
    # def indic_name(self):
    #     return self.indic_fmt.format(**self.dict())

    @property
    def names(self):
        names = [fmt.format(**self.dict())
                 for fmt in self.names_fmt.values()]
        if self.offset > 0:
            names = [self.offset_fmt.format(name=name,
                                            offset=-self.offset)
                     for name in names]
        return names


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

        if not self.offset:
            return indic
        
        indic_offset = indic.shift(self.offset)
        indic_offset.columns = self.names

        return indic_offset
    
    def compute(self, *data, offset=None, **kwrds):

        if not (offset is None):
            self.offset = offset

        # raise NotImplementedError(
        #     "Generic indicator type doesn't have a compute indicator implementation")

    def plotly(self, ohlcv_df, plot_ohlcv=False):

        var_open = self.ohlcv_names.get("open", "open")
        var_high = self.ohlcv_names.get("high", "high")
        var_low = self.ohlcv_names.get("low", "low")
        var_close = self.ohlcv_names.get("close", "close")

        if plot_ohlcv:
            fig = make_subplots(rows=2, cols=1,
                                shared_xaxes=True,
                                vertical_spacing=0.02)

            fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                         open=ohlcv_df[var_open],
                                         high=ohlcv_df[var_high],
                                         low=ohlcv_df[var_low],
                                         close=ohlcv_df[var_close], name="OHLC"),
                          row=1, col=1)
        else:
            fig = go.Figure()

        return fig
            



class IndicatorOHLCV(Indicator):

    ohlcv_names: dict = Field(
        {v: v for v in ["open", "high", "low", "close", "volume"]},
        description="OHLCV variable name dictionnary")
