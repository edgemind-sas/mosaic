# Technical analysis librairie
# ============================
import pandas as pd
import numpy as np
import itertools

# Misc functions
# --------------


def lag(data, n=0, lag_fmt="{name}[{n}]"):
    """Lag operator
    lag(data_t, n) = data_{t-n}
    """
    data_lag = data.shift(n)
    if isinstance(data_lag, pd.DataFrame):
        data_lag.columns = [lag_fmt.format(
            name=col, n=-n) for col in data_lag.columns]
    else:
        data_lag.name = lag_fmt.format(name=data_lag.name, n=-n)

    return data_lag


def prepare_returns_indic(ret_dfd, indic):
    if isinstance(ret_dfd, pd.DataFrame):
        ret_dfd = {"close": ret_dfd}

    indic_names = list(indic.columns) if isinstance(indic, pd.DataFrame)\
        else [indic.name]

    ret_indic_list = []
    for ret_name, ret_df in ret_dfd.items():

        ret_indic_df = ret_df.stack().rename("returns")\
                                     .reset_index(-1)\
                                     .join(indic)
        ret_indic_df["measure"] = ret_name
        var_order = ["measure"] + indic_names + ["period", "returns"]
        ret_indic_list.append(ret_indic_df[var_order])

    ret_indic_df = pd.concat(ret_indic_list, axis=0)

    return ret_indic_df


def compute_combinations(**params_dict):
    keys, values = zip(*params_dict.items())
    return [dict(zip(keys, v)) for v in itertools.product(*values)]
