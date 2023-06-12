import logging
import pydantic
import typing


class InvestModel(pydantic.BaseModel):

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

    # def compute(ohlcv_df, indic_df, **kwrds):
    #     raise NotImplementedError("compute method not implemented")

