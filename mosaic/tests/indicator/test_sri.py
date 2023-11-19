# from databayes.modelling import DFPotential, DFVariable, DFCPD
# from databayes.utils import Discretizer
import mosaic.indicator as mid
import logging
import pytest
import pkg_resources
import pandas as pd
import numpy as np
import os
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


def test_sri_001():

    indic = mid.SRI()


def test_sri_002(data_btc_usdc_20_df):

    indic = mid.SRI()
    assert indic.names() == ['SRI_close_1', 'SRI_HL_low_1', 'SRI_HH_high_1']

    indic_df = indic.compute(data_btc_usdc_20_df)

    indic_expect = [[0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0], [0.0, 1.0, 1.0]]

    np.testing.assert_allclose(indic_df, indic_expect)


def test_sri_003(data_btc_usdc_20_df):

    indic = mid.SRI(length=2)

    assert indic.names() == ['SRI_close_2', 'SRI_HL_low_2', 'SRI_HH_high_2']

    indic_df = indic.compute(data_btc_usdc_20_df)

    indic_expect = [[np.nan, 0.0, 0.0], [1.0, 1.0, 1.0], [-1.0, 1.0, 2.0], [1.0, 2.0, 2.0], [-1.0, 2.0, 2.0], [1.0, 2.0, 2.0], [-1.0, 1.0, 1.0], [1.0, 1.0, 2.0], [1.0, 2.0, 2.0], [-1.0, 1.0, 2.0], [-1.0, 2.0, 2.0], [1.0, 2.0, 1.0], [1.0, 2.0, 2.0], [-1.0, 2.0, 2.0], [-1.0, 1.0, 2.0], [-1.0, 1.0, 2.0], [-1.0, 1.0, 2.0], [-1.0, 2.0, 2.0], [-1.0, 1.0, 2.0]]

    np.testing.assert_allclose(indic_df, indic_expect)


def test_sri_004(data_btc_usdc_20_df):

    indic = mid.SRI(length=3)

    assert indic.names() == ['SRI_close_3', 'SRI_HL_low_3', 'SRI_HH_high_3']

    indic_df = indic.compute(data_btc_usdc_20_df)

    indic_expect = [[np.nan, 0.0, 0.0], [np.nan, 0.0, 0.0], [-0.8222404259677658, 2.0, 2.0], [1.0, 2.0, 2.0], [0.04270235818997348, 3.0, 3.0], [0.7159343098093871, 3.0, 2.0], [-1.0, 2.0, 2.0], [-0.8555691554467328, 1.0, 1.0], [1.0, 1.0, 3.0], [-1.0, 1.0, 3.0], [-1.0, 2.0, 2.0], [1.0, 3.0, 2.0], [1.0, 3.0, 2.0], [-1.0, 3.0, 3.0], [-1.0, 1.0, 2.0], [-1.0, 1.0, 2.0], [-1.0, 1.0, 2.0], [-1.0, 2.0, 3.0], [-1.0, 1.0, 2.0]]

    np.testing.assert_allclose(indic_df, indic_expect)



def test_sri_005(data_btc_usdc_20_df):

    indic = mid.SRI(length=10)

    assert indic.names() == ['SRI_close_10', 'SRI_HL_low_10', 'SRI_HH_high_10']

    indic_df = indic.compute(data_btc_usdc_20_df)

    indic_expect = [[np.nan, 0.0, 0.0], [np.nan, 0.0, 0.0], [np.nan, 0.0, 0.0], [np.nan, 0.0, 0.0], [np.nan, 0.0, 0.0], [np.nan, 0.0, 0.0], [np.nan, 0.0, 0.0], [np.nan, 0.0, 0.0], [np.nan, 0.0, 0.0], [-1.0, 2.0, 3.0], [-1.0, 3.0, 3.0], [-0.6568888888888371, 4.0, 3.0], [-0.5700740740740138, 5.0, 2.0], [-0.9558320373250953, 6.0, 2.0], [-1.0, 2.0, 1.0], [-1.0, 1.0, 6.0], [-1.0, 1.0, 5.0], [-1.0, 2.0, 4.0], [-1.0, 1.0, 4.0]]

    np.testing.assert_allclose(indic_df, indic_expect)
