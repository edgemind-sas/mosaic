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
def data_btc_usdc_1000_df():

    data_filename = os.path.join(DATA_PATH, "data_btc_usdc_1000.csv")
    data_df = pd.read_csv(data_filename, sep=",", index_col="timestamp")
    return data_df

# =============== Tests begin here ================== #

def test_pm_base_001():

    model = mpm.PredictModelBase()

    assert 'bkd' not in model.dict()
    assert 'logger' not in model.dict()

def test_pm_base_002():

    class MockIndicator(mid.IndicatorOHLCV):
        length: int
        
        @property
        def bw_length(self):
            return self.length

    model = mpm.PredictModelBase(
        features=[MockIndicator(length=5),
                  MockIndicator(length=7)])

    assert model.bw_length == 7


def test_pm_base_003():

    features_th_df = pd.DataFrame([5, 6, 7])
    
    class MockIndicator(mid.IndicatorOHLCV):
        def compute(self, _):
            return features_th_df

    model = mpm.PredictModelBase(
        features=[MockIndicator()])

    features_df = model.compute_features(pd.DataFrame())
    assert features_df.equals(features_th_df)

    features_df = model.fit(pd.DataFrame())
    assert features_df.equals(features_th_df.shift(1).dropna())


def test_pm_base_004():
    with pytest.raises(ValueError):
        mpm.PMReturnsUpDown(direction="invalid",
                            threshold_mode="normal",
                            threshold=0)

    with pytest.raises(ValueError):
        mpm.PMReturnsUpDown(
            direction="up",
            threshold_mode="invalid",
            threshold=0)


def test_pm_base_005():
    ohlcv_df = pd.DataFrame({'close': [1, 2, 3, 4, 5, 6]})
    model = mpm.PMReturnsUpDown(
        returns_horizon=1,
        direction="up",
        threshold=0.5,
        threshold_mode="normal"
    )
    ret_th = ohlcv_df["close"].pct_change(2).shift(-1) > 0.5
    ret = model.compute_returns(ohlcv_df)
    assert ret.equals(ret_th)
