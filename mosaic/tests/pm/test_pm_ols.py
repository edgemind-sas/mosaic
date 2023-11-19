import mosaic.predict_model as mpm
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
    data_df = pd.read_csv(data_filename, sep=",", index_col="timestamp")
    return data_df

# =============== Tests begin here ================== #

def test_pm_ols_001(data_btc_usdc_20_df):

    # Test data
    data_df = data_btc_usdc_20_df.copy()
    model_params = dict(
        features=[mid.SRI(length=5)],
        standard_features=False,
    )

    # Expected results
    features_df_filename = \
        os.path.join(EXPECTED_PATH, "test_pm_ols_001_features_df.csv")
    target_s_filename = \
        os.path.join(EXPECTED_PATH, "test_pm_ols_001_target_s.csv")

    # Test running
    model = mpm.PMOLS(**model_params)
    features_df = model.compute_features(data_df)
    features_prep_df, target_s = model.prepare_data(data_df)
    model.fit(data_df)
    
    # features_df.to_csv(features_df_filename)
    features_expect_df = pd.read_csv(features_df_filename,
                                     index_col="datetime")
    #target_s.to_csv(target_s_filename)
    target_expect_s = pd.read_csv(target_s_filename,
                                  index_col="datetime")\
                        .squeeze("columns")

    # Assertions
    assert model.bw_length == 5
    assert not model.standard_features
    assert model.features_center is None
    assert model.features_std is None

    pd.testing.assert_frame_equal(
        features_df,
        features_expect_df,
        check_exact=False,
        check_dtype=False)

    pd.testing.assert_frame_equal(
        features_expect_df.shift(1).dropna(),
        features_prep_df,
        check_exact=False,
        check_dtype=False)

    pd.testing.assert_series_equal(
        target_s,
        target_expect_s,
        check_exact=False,
        check_dtype=False)

    assert model.bkd.rsquared == pytest.approx(0.08689851834472195)
