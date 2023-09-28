import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pkg_resources

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


def plotly_ohlcv(ohlcv_df, fig=None, ohlcv_names={}, trace_params={}, layout={}):
    open_var = ohlcv_names.get("open", "open")
    high_var = ohlcv_names.get("high", "high")
    low_var = ohlcv_names.get("low", "low")
    close_var = ohlcv_names.get("close", "close")
    volume_var = ohlcv_names.get("volume", "volume")

    if fig is None:
        fig = go.Figure()

    fig.add_trace(go.Candlestick(x=ohlcv_df.index,
                                 open=ohlcv_df[open_var],
                                 high=ohlcv_df[high_var],
                                 low=ohlcv_df[low_var],
                                 close=ohlcv_df[close_var], name="OHLC"),
                  **trace_params)

    # PROBLEM: secondary_y does not work...
    # # include a go.Bar trace for volumes
    # fig.add_trace(go.Bar(x=ohlcv_df.index,
    #                      y=ohlcv_df[volume_var], name="Volume"),
    #               secondary_y=True)
    # fig.layout.yaxis2.showgrid = False

    fig.update_layout(**layout)

    # fig.for_each_trace(
    #     lambda trace: trace.update(
    #         visible=True) if trace.name == "Volume"
    #     else trace.update(visible=False)
    # )

    return fig


def plotly_indic(indic, fig=None, trace_params={}, layout={}):

    if fig is None:
        fig = go.Figure()

    fig.add_trace(go.Scatter(x=indic.index,
                             y=indic,
                             mode="markers" if indic.dtype.name == "category" else "lines",
                             name=indic.name),
                  **trace_params)

    if indic.dtype.name == "category":
        fig.update_yaxes(categoryorder='array',
                         categoryarray=indic.cat.categories)

    fig.update_layout(**layout)

    return fig


def plotly_ohlcv_indics(ohlcv_df, indic_dict={},
                        ohlcv_params={},
                        indic_params_dict={},
                        layout={}):

    nb_indics = len(indic_dict)

    secondaryy_specs = [[{"secondary_y": True}]] + \
        [[{"secondary_y": False}]*nb_indics]
    fig = make_subplots(rows=nb_indics + 1, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.02,
                        specs=secondaryy_specs)

    ohlcv_params.setdefault("layout", {})
    ohlcv_params["layout"]["xaxis_rangeslider_visible"] = False
    plotly_ohlcv(ohlcv_df, fig=fig,
                 trace_params=dict(row=1, col=1),
                 **ohlcv_params)

    for i, (indic_id, indic) in enumerate(indic_dict.items()):
        plotly_indic(indic, fig=fig, trace_params=dict(row=i+2, col=1),
                     **indic_params_dict.get(indic_id, {}))

    fig.update_layout(**layout)

    return fig
