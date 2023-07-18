# from databayes.modelling import DFPotential, DFVariable, DFCPD
# from databayes.utils import Discretizer
import mosaic.indicator as mid
import logging
import pytest
import pkg_resources
import pandas as pd
import numpy as np
import os
import json
import yaml
import pathlib

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb


logger = logging.getLogger()

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
EXPECTED_PATH = os.path.join(os.path.dirname(__file__), "expected")
pathlib.Path(DATA_PATH).mkdir(parents=True, exist_ok=True)
pathlib.Path(EXPECTED_PATH).mkdir(parents=True, exist_ok=True)



@pytest.fixture
def data_btc_usdc_20_df():

    data_filename = os.path.join(DATA_PATH, "data_btc_usdc_20.csv")
    data_df = pd.read_csv(data_filename, sep=",", index_col="datetime")
    return data_df

@pytest.fixture
def data_btc_usdc_1000_df():

    data_filename = os.path.join(DATA_PATH, "data_btc_usdc_1000.csv")
    data_df = pd.read_csv(data_filename, sep=",", index_col="datetime")
    return data_df


# @pytest.fixture
# def data_btc_1000_hammer_df(data_btc_usdc_1000_df):

#     disc_specs = yaml.load("""
#       variables:
#         ret_close_t.:
#           params:
#             bins: [-.inf, 0, .inf]

#         hammer:
#           params:
#             bins: [-.inf, -2, 2, .inf]
#             labels: [LL, M, HH]

#     """, Loader=yaml.SafeLoader())
#     data_disc_df = Discretizer(**disc_specs).discretize(data_btc_usdc_1000_df)
#     return data_disc_df[["ret_close_t2", "mvq50", "hammer"]]

# =============== Tests begin here ================== #


def test_rsi_001():

    indic = mid.RSI()


def test_rsi_002(data_btc_usdc_20_df):

    indic = mid.RSI()

    assert indic.mode == "classic"
    assert indic.offset == 0
    assert indic.names == ['RSI_0']

    indic_df = indic.compute(data_btc_usdc_20_df)

    assert isinstance(indic_df, pd.DataFrame)
    assert indic_df.isna().all(None)


def test_rsi_003(data_btc_usdc_20_df):

    indic = mid.RSI(length=1)

    assert indic.names == ['RSI_1']

    indic_cla_df = indic.compute(data_btc_usdc_20_df)

    assert isinstance(indic_cla_df, pd.DataFrame)

    indic.mode = "wilder"
    assert indic.mode == "wilder"
    
    indic_wil_df = indic.compute(data_btc_usdc_20_df)

    np.testing.assert_allclose(indic_cla_df, indic_wil_df)


def test_rsi_004(data_btc_usdc_20_df):

    indic = mid.RSI(length=2)

    assert indic.names == ['RSI_2']
    assert indic.offset == 0

    indic_cla_off0_df = indic.compute(data_btc_usdc_20_df)

    indic.offset = 1
    assert indic.offset == 1
    assert indic.names == ['RSI_2[-1]']

    indic_cla_off1_df = indic.compute(data_btc_usdc_20_df)

    np.testing.assert_allclose(indic_cla_off0_df.shift(1), indic_cla_off1_df)

