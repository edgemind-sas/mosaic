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

# =============== Tests begin here ================== #


def test_candle_001():

    indic = mid.Candle()


def test_candle_002(data_btc_usdc_20_df):

    # Test data
    data = data_btc_usdc_20_df.copy()
    indic_params = {}

    # Expected results
    indic_expect_filenames = os.path.join(EXPECTED_PATH, "test_candle_002.csv")
    
    # Test running
    indic = mid.Candle(**indic_params)
    indic_df = indic.compute(data)
    #indic_df.to_csv(indic_expect_filenames)
    indic_expect_df = pd.read_csv(indic_expect_filenames, index_col="datetime")

    assert set(indic.names()) == set(indic_df.columns)
    assert indic.bw_length == 1    
    np.testing.assert_allclose(indic_df, indic_expect_df)


def test_candle_003(data_btc_usdc_20_df):

    # Test data
    data = data_btc_usdc_20_df.copy()
    indic_params = dict(
        variation_length=1,
    )

    # Expected results
    indic_expect_filenames = os.path.join(EXPECTED_PATH, "test_candle_003.csv")

    # Test running
    indic = mid.Candle(**indic_params)
    indic_df = indic.compute(data)
    #indic_df.to_csv(indic_expect_filenames)
    indic_expect_df = pd.read_csv(indic_expect_filenames, index_col="datetime")

    ipdb.set_trace()

    # Assertions
    assert set(indic.names()) == set(indic_df.columns)
    assert indic.bw_length == 2
    np.testing.assert_allclose(indic_df, indic_expect_df)
