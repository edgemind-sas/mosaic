# Technical analysis librairie
# ============================
import pandas as pd
from . import prepare_returns_indic

# Empirical conditional distribution
# ----------------------------------


def eval_returns_emp_quantiles(ret_dfd, indic,
                               quantiles=[0.05, 0.25, 0.5, 0.75, 0.95]):

    indic_names = list(indic.columns) if isinstance(indic, pd.DataFrame)\
        else [indic.name]

    var_grp = ["measure"] + indic_names + ["period"]

    ret_indic_df = prepare_returns_indic(ret_dfd, indic)

    ret_indic_quantiles_df = ret_indic_df.groupby(
        var_grp)["returns"].quantile(quantiles)
    ret_indic_quantiles_df.index.rename("quantiles", level=-1, inplace=True)

    var_grp = var_grp + ["quantiles", "returns"]
    ret_indic_quantiles_df = ret_indic_quantiles_df.reset_index()[var_grp]

    cat_type = pd.api.types.CategoricalDtype(
        categories=quantiles, ordered=True)
    ret_indic_quantiles_df["quantiles"] = ret_indic_quantiles_df["quantiles"].astype(
        cat_type)

    return ret_indic_quantiles_df


def eval_ers(ret_dfd, indic,
             quantiles=[0.05, 0.25, 0.5, 0.75, 0.95]):
    """Extreme returns score."""

    quantiles_bis = list(set([1 - q for q in quantiles] + quantiles))

    indic_names = list(indic.columns) if isinstance(indic, pd.DataFrame)\
        else [indic.name]

    var_index = ["measure", "quantiles"] + indic_names + ["period"]

    ret_indic_quantiles_df = \
        eval_returns_emp_quantiles(ret_dfd, indic,
                                   quantiles=quantiles_bis).set_index(var_index)

    indic_risk_df_list = []
    for q in quantiles:
        indic_risk_cur_df = \
            ((1-q)*ret_indic_quantiles_df.loc[("high", q)] + q *
             ret_indic_quantiles_df.loc[("low", 1-q)]).reset_index()
        indic_risk_cur_df["risk"] = q
        # return indic_risk_cur_df

        indic_risk_df_list.append(indic_risk_cur_df)

    indic_risk_df = pd.concat(indic_risk_df_list, axis=0)

    return indic_risk_df
