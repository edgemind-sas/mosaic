# Technical analysis librairie
# ============================
import pandas as pd
import numpy as np
import itertools
import pydantic
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


# Misc classes
# ------------

class ValueNeighborhood(pydantic.BaseModel):

    lower_bound: float = \
        pydantic.Field(-float("inf"), description="Lower bound")
    upper_bound: float = \
        pydantic.Field(float("inf"), description="Upper bound")
    delta: float = \
        pydantic.Field(0, description="+/- delta from current value")
    step: float = \
        pydantic.Field(1, description="Neighborhood discretization step")

    def domain_from_value(self, value):

        lower_bound = \
            max(value - self.delta, self.lower_bound)
        upper_bound = \
            min(value + self.delta, self.upper_bound)

        if value.__class__ == int:
            dom = list(range(int(lower_bound),
                             int(upper_bound) + 1,
                             int(self.step)))
        else:
            dom = list(np.arange(lower_bound, upper_bound, self.step))

        return dom
    
    def random_neighbor_from_value(self, value):

        lower_bound = \
            max(value - self.delta, self.lower_bound)
        upper_bound = \
            min(value + self.delta, self.upper_bound)
        
        value_new = \
            np.random.uniform(lower_bound, upper_bound)
            
        if value.__class__ == int:
            value_new = round(value_new)

        return value_new


# Misc functions
# --------------

def lag(data, n=0, lag_fmt="{name}[{n}]"):
    """Lag operator
    lag(data_t, n) = data_{t-n}
    """
    warnings.warn("lag is deprecated use Indicator.apply_offset instead",
                  DeprecationWarning)

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


def join_obj_columns(data_df, sep="|"):

    var_to_joined = data_df.columns
    var_names_joined = sep.join(var_to_joined)
    
    data_join = data_df[var_to_joined[0]].astype(str)
    for var in var_to_joined[1:]:
        data_join = data_join.str.cat(
                data_df[var].astype(str), sep="|")

    data_join.name = var_names_joined

    return data_join


