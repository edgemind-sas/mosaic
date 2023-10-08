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


def test_returns_001():

    indic = mid.Returns()


def test_returns_002():

    indic = mid.Returns()

    assert indic.names() == ['ret_close_0']
    assert indic.bw_length == 1

def test_returns_003(data_btc_usdc_20_df):

    indic = mid.Returns()

    indic_df = indic.compute(data_btc_usdc_20_df)

    np.testing.assert_allclose(
        indic_df,
        data_btc_usdc_20_df[["close"]].pct_change(1),
        )
    
    assert isinstance(indic_df, pd.DataFrame)


def test_returns_003(data_btc_usdc_20_df):

    indic = mid.Returns(horizon=-3)

    indic_df = indic.compute(data_btc_usdc_20_df)

    np.testing.assert_allclose(
        indic_df,
        data_btc_usdc_20_df[["close"]].pct_change(4),
        )
    


def test_returns_004(data_btc_usdc_20_df):

    indic = mid.Returns(horizon=1, var="volume")

    indic_df = indic.compute(data_btc_usdc_20_df)

    np.testing.assert_allclose(
        indic_df,
        data_btc_usdc_20_df[["volume"]].pct_change(2).shift(-1),
        )
    


def test_returns_005(data_btc_usdc_20_df):

    indic = mid.Returns(horizon=-3, var="volume")

    indic_df = indic.compute(data_btc_usdc_20_df)

    np.testing.assert_allclose(
        indic_df,
        data_btc_usdc_20_df[["volume"]].pct_change(4),
        )


def test_returns_rolling_001(data_btc_usdc_20_df):

    indic = mid.ReturnsRolling(var="high")

    indic_df = indic.compute(data_btc_usdc_20_df)

    assert indic.names('ret') == "ret_max_close_high_0"
    
    result_expected = [np.nan, 0.001362117146921804, 0.00010784730327961789, 0.0014502778981255737, 0.0002350424017567576, 0.0006027622116528963, -0.0002312973251809014, 0.0012167219281407071, 0.0009249759667815383, 0.0003855092666251725, 2.7210187925508222e-05, 0.0013171762586050573, 0.0006210802055328646, 0.00015970143103793966, 8.863456963736915e-05, 0.00045228379041328814, 0.0009544607472280475, 0.0012184867480449224, 0.0002491305425129653]
    
    np.testing.assert_allclose(
        indic_df[indic.names('ret')],
        result_expected,
        )


def test_returns_rolling_002(data_btc_usdc_20_df):

    indic = mid.ReturnsRolling(var="high", horizon=-2)

    indic_df = indic.compute(data_btc_usdc_20_df)

    assert indic.names('ret') == "ret_max_close_high_-2"
    
    result_expected = [np.nan, np.nan, np.nan, 0.0015673234074902176, 0.00030444675140262056, 0.001502785174422483, 0.0002350424017567576, 0.0006027622116528963, -0.00010327694519718378, 0.0012167219281407071, 0.0009249759667815383, 0.000551881282528921, 0.0012856140275254724, 0.0013171762586050573, 0.0006210802055328646, 0.00015970143103793966, 8.863456963736915e-05, 0.00045228379041328814, 0.0009544607472280475]
    
    np.testing.assert_allclose(
        indic_df[indic.names('ret')],
        result_expected,
        )


def test_returns_rolling_003(data_btc_usdc_20_df):

    indic = mid.ReturnsRolling(fun="min", var="low", horizon=-4)

    indic_df = indic.compute(data_btc_usdc_20_df)

    assert indic.names('ret') == "ret_min_close_low_-4"
    
    result_expected = [np.nan, np.nan, np.nan, np.nan, np.nan, -0.00033285424942575137, -0.0018213015905458318, -0.0006255097581405744, -0.0018905584489136151, -0.0013772040175177303, -0.0030049825747050507, -0.0016888143451461168, -0.0017839783929922692, -0.0020411531142122685, -0.0013093219140346557, -0.002557299457287776, -0.003452300986348633, -0.0035309366987156254, -0.0036380584449345887]
    
    np.testing.assert_allclose(
        indic_df[indic.names('ret')],
        result_expected,
        )

