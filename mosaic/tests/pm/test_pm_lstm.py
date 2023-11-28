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
from sklearn.preprocessing import MinMaxScaler

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
    data_df = pd.read_csv(data_filename, sep=",", index_col="datetime",
                          parse_dates=["datetime"]).drop("timestamp", axis=1)
    return data_df

@pytest.fixture
def data_btc_usdc_1000_df():

    data_filename = os.path.join(DATA_PATH, "data_btc_usdc_1000.csv")
    data_df = pd.read_csv(data_filename, sep=",", index_col="datetime",
                          parse_dates=["datetime"]).drop("timestamp", axis=1)
    return data_df

@pytest.fixture
def data_btc_usdc_800_df():

    data_filename = os.path.join(DATA_PATH, "data_btc_usdc_800.csv")
    data_df = pd.read_csv(data_filename, sep=",", index_col="datetime",
                          parse_dates=["datetime"]).drop("timestamp", axis=1)
    return data_df

@pytest.fixture
def data_btc_usdc_200_df():

    data_filename = os.path.join(DATA_PATH, "data_btc_usdc_200.csv")
    data_df = pd.read_csv(data_filename, sep=",", index_col="datetime",
                          parse_dates=["datetime"]).drop("timestamp", axis=1)
    return data_df


# =============== Tests begin here ================== #

def test_pm_gen(model_params,
                train_df, test_df, test_id,
                expected_results={},
                update_expect=False):

    # Expected results
    target_train_expect_filename = \
        os.path.join(EXPECTED_PATH,
                     f"test_pm_{test_id}_target_train_expect.csv")
    features_train_comp_expect_filename = \
        os.path.join(EXPECTED_PATH,
                     f"test_pm_{test_id}_features_train_comp_expect.csv")
    features_train_prep_fit_expect_filename = \
        os.path.join(EXPECTED_PATH,
                     f"test_pm_{test_id}_features_train_prep_fit_expect.npy")
    target_train_prep_fit_expect_filename = \
        os.path.join(EXPECTED_PATH,
                     f"test_pm_{test_id}_target_train_prep_fit_expect.npy")
    target_train_pred_expect_filename = \
        os.path.join(EXPECTED_PATH,
                     f"test_pm_{test_id}_target_train_pred_expect.csv")
    target_test_pred_expect_filename = \
        os.path.join(EXPECTED_PATH,
                     f"test_pm_{test_id}_target_test_pred_expect.csv")
    target_test_pred_one_expect_filename = \
        os.path.join(EXPECTED_PATH,
                     f"test_pm_{test_id}_target_test_pred_one_expect.csv")

    # Test running
    tdelta = train_df.index[1] - train_df.index[0]
    
    model = mpm.PMLSTM(**model_params)
    target_train_s = model.compute_returns(train_df)
    features_train_comp_df = model.compute_features(train_df)
    features_train_prep_fit_arr, target_train_prep_fit_arr = \
        model.prepare_data_fit(train_df)

    model.fit(train_df)

    dte = test_df.index[-1]
    dts = dte - tdelta*(model.bw_length - 1)
    test_one_df = test_df.loc[dts:dte]
    target_test_pred_one_s = model.predict(test_one_df)
    
    target_train_pred_s = model.predict(train_df)
    mae_train = \
        (target_train_s - target_train_pred_s).abs().mean()

    target_test_pred_s = model.predict(test_df)
    target_test_s = model.compute_returns(test_df)
   
    mae_test = \
        (target_test_s - target_test_pred_s).abs().mean()

    acc_test_df = \
        pd.concat([target_test_s, target_test_pred_s], axis=1).dropna() > 0
    dirpred_test = (acc_test_df.iloc[:, 0] == acc_test_df.iloc[:, 1])
    acc_test = dirpred_test.mean()
    ngp_test = dirpred_test.sum()
    
    # Get expected results
    if update_expect:
        target_train_s.to_csv(target_train_expect_filename)
        features_train_comp_df.to_csv(features_train_comp_expect_filename)
        np.save(features_train_prep_fit_expect_filename,
                features_train_prep_fit_arr)
        np.save(target_train_prep_fit_expect_filename,
                target_train_prep_fit_arr)
        target_train_pred_s.to_csv(target_train_pred_expect_filename)
        target_test_pred_s.to_csv(target_test_pred_expect_filename)
        target_test_pred_one_s.to_csv(target_test_pred_one_expect_filename)

        print(f"mae_train={mae_train},")
        print(f"mae_test={mae_test},")
        print(f"acc_test={acc_test},")
        print(f"ngp_test={ngp_test},")

    target_train_expect_s = pd.read_csv(target_train_expect_filename,
                                        parse_dates=["datetime"],
                                        index_col="datetime")\
                              .squeeze("columns")
    features_train_comp_expect_df = \
        pd.read_csv(features_train_comp_expect_filename,
                    parse_dates=["datetime"],
                    index_col="datetime")
    features_train_prep_expect_arr = \
        np.load(features_train_prep_fit_expect_filename)
    target_prep_expect_arr = np.load(target_train_prep_fit_expect_filename)
    target_train_pred_expect_s = pd.read_csv(target_train_pred_expect_filename,
                                             parse_dates=["datetime"],
                                             index_col="datetime")\
                                   .squeeze("columns")
    target_test_pred_expect_s = pd.read_csv(target_test_pred_expect_filename,
                                            parse_dates=["datetime"],
                                            index_col="datetime")\
                                  .squeeze("columns")
    target_test_pred_one_expect_s = \
        pd.read_csv(target_test_pred_one_expect_filename,
                    parse_dates=["datetime"],
                    index_col="datetime")\
          .squeeze("columns")

    # ipdb.set_trace()
    
    # Assertions
    if model_bw_length_expect := expected_results.get("model_bw_length"):
        assert model.bw_length == model_bw_length_expect
        
    pd.testing.assert_series_equal(
        target_train_s,
        target_train_expect_s,
        check_exact=False,
        check_dtype=False)

    pd.testing.assert_frame_equal(
        features_train_comp_df,
        features_train_comp_expect_df,
        check_exact=False,
        check_dtype=False)

    np.testing.assert_almost_equal(
        features_train_prep_fit_arr,
        features_train_prep_expect_arr)

    np.testing.assert_almost_equal(
        target_train_prep_fit_arr,
        target_prep_expect_arr)

    pd.testing.assert_series_equal(
        target_train_pred_s,
        target_train_pred_expect_s,
        check_exact=False,
        check_dtype=False)

    pd.testing.assert_series_equal(
        target_test_pred_s,
        target_test_pred_expect_s,
        check_exact=False,
        check_dtype=False)

    assert len(target_test_pred_one_s) == len(test_one_df) - model.params.seq_length + 1

    pd.testing.assert_series_equal(
        target_test_pred_one_s,
        target_test_pred_one_expect_s,
        check_exact=False,
        check_dtype=False)

    if mae_train_expect := expected_results.get("mae_train"):
        assert mae_train == pytest.approx(mae_train_expect)

    if mae_test_expect := expected_results.get("mae_test"):
        assert mae_test == pytest.approx(mae_test_expect)

    if acc_test_expect := expected_results.get("acc_test"):
        assert acc_test == pytest.approx(acc_test_expect)

    if ngp_test_expect := expected_results.get("ngp_test"):
        assert ngp_test == pytest.approx(ngp_test_expect)


def test_pm_lstm_001(data_btc_usdc_20_df):

    # Test data
    test_id = "lstm_001"
    update_expect = False
    train_df = data_btc_usdc_20_df.copy()
    test_df = data_btc_usdc_20_df.copy()

    model_params = dict(
        features=[mid.SRI(length=5)],
        params=dict(seed=56),
    )

    expected_results = dict(
        mae_train=0.003700136416043736,
        mae_test=0.003700136416043736,
    )

    test_pm_gen(model_params=model_params,
                train_df=train_df,
                test_df=test_df,
                test_id=test_id,
                expected_results=expected_results,
                update_expect=update_expect)

    
def test_pm_lstm_002(data_btc_usdc_20_df):

    # Test data
    test_id = "lstm_002"
    update_expect = False
    train_df = data_btc_usdc_20_df.copy()
    test_df = data_btc_usdc_20_df.copy()

    model_params = dict(
        features=[mid.SRI(length=5)],
        params=dict(
            seed=56,
            seq_length=2,
        ),
    )

    expected_results = dict(
        mae_train=0.0017976741678489795,
        mae_test=0.0017976741678489795,
    )

    test_pm_gen(model_params=model_params,
                train_df=train_df,
                test_df=test_df,
                test_id=test_id,
                expected_results=expected_results,
                update_expect=update_expect)


def test_pm_lstm_003(data_btc_usdc_800_df,
                     data_btc_usdc_200_df,
                     ):

    # Test data
    test_id = "lstm_003"
    update_expect = False
    train_df = data_btc_usdc_800_df.copy()
    test_df = data_btc_usdc_200_df.copy()

    model_params = dict(
        features=[mid.SRI(length=5)],
        params=dict(
            seed=56,
            seq_length=2,
        ),
    )

    expected_results = dict(
        mae_train=0.001030562533852949,
        mae_test=0.0008986122104143214,
        acc_test=0.4587628865979381,
    )

    test_pm_gen(model_params=model_params,
                train_df=train_df,
                test_df=test_df,
                test_id=test_id,
                expected_results=expected_results,
                update_expect=update_expect)


def test_pm_lstm_004(data_btc_usdc_800_df,
                     data_btc_usdc_200_df,
                     ):

    # Test data
    test_id = "lstm_004"
    update_expect = False
    train_df = data_btc_usdc_800_df.copy()
    test_df = data_btc_usdc_200_df.copy()

    model_params = dict(
        features=[mid.Candle()],
        params=dict(
            seed=56,
            seq_length=2,
        ),
    )

    expected_results = dict(
        mae_train=0.001604737409598406,
        mae_test=0.0014456046279729474,
        acc_test=0.5303030303030303,
    )

    test_pm_gen(model_params=model_params,
                train_df=train_df,
                test_df=test_df,
                test_id=test_id,
                expected_results=expected_results,
                update_expect=update_expect)


def test_pm_lstm_005(data_btc_usdc_800_df,
                     data_btc_usdc_200_df,
                     ):

    # Test data
    test_id = "lstm_005"
    update_expect = False
    train_df = data_btc_usdc_800_df.copy()
    test_df = data_btc_usdc_200_df.copy()

    model_params = dict(
        features=[mid.Candle()],
        params=dict(
            seed=56,
            seq_length=3,
        ),
    )

    expected_results = dict(
        mae_train=0.0010171370362043219,
        mae_test=0.0008416777100885746,
        acc_test=0.5329949238578681,
    )

    test_pm_gen(model_params=model_params,
                train_df=train_df,
                test_df=test_df,
                test_id=test_id,
                expected_results=expected_results,
                update_expect=update_expect)


def test_pm_lstm_006(data_btc_usdc_800_df,
                     data_btc_usdc_200_df,
                     ):

    # Test data
    test_id = "lstm_006"
    update_expect = False
    train_df = data_btc_usdc_800_df.copy()
    test_df = data_btc_usdc_200_df.copy()

    model_params = dict(
        features=[mid.Candle(
            variation_length=1,
        )],
        params=dict(
            seed=56,
            seq_length=3,
        ),
    )

    expected_results = dict(
        mae_train=0.0020865835737300126,
        mae_test=0.0021756894811307674,
        acc_test=0.4318181818181818,
    )

    test_pm_gen(model_params=model_params,
                train_df=train_df,
                test_df=test_df,
                test_id=test_id,
                expected_results=expected_results,
                update_expect=update_expect)


def test_pm_lstm_007(data_btc_usdc_800_df,
                     data_btc_usdc_200_df,
                     ):

    # Test data
    test_id = "lstm_007"
    update_expect = False
    train_df = data_btc_usdc_800_df.copy()
    test_df = data_btc_usdc_200_df.copy()

    model_params = dict(
        features=[mid.Candle()],
        sk_preproc="MinMaxScaler",
        sk_preproc_params={"feature_range": (0, 1)},
        params=dict(
            seed=56,
            seq_length=3,
        ),
    )

    expected_results = dict(
        mae_train=0.0010066413836890935,
        mae_test=0.0008450049848962418,
        acc_test=0.5025380710659898,
    )

    test_pm_gen(model_params=model_params,
                train_df=train_df,
                test_df=test_df,
                test_id=test_id,
                expected_results=expected_results,
                update_expect=update_expect)


def test_pm_lstm_008(data_btc_usdc_800_df,
                     data_btc_usdc_200_df,
                     ):

    # Test data
    test_id = "lstm_008"
    update_expect = False
    train_df = data_btc_usdc_800_df.copy()
    test_df = data_btc_usdc_200_df.copy()

    model_params = dict(
        features=[mid.Candle(
            variation_length=5,
        )],
        sk_preproc="MinMaxScaler",
        sk_preproc_params={"feature_range": (0, 1)},
        params=dict(
            seed=56,
            seq_length=5,
            units=100,
            batch_size=100,
        ),
    )

    expected_results = dict(
        mae_train=0.0005239116788741979,
        mae_test=0.0004272671473713463,
        acc_test=0.75,
    )

    test_pm_gen(model_params=model_params,
                train_df=train_df,
                test_df=test_df,
                test_id=test_id,
                expected_results=expected_results,
                update_expect=update_expect)


def test_pm_lstm_009(data_btc_usdc_800_df,
                     data_btc_usdc_200_df,
                     ):

    # Test data
    test_id = "lstm_009"
    update_expect = False
    train_df = data_btc_usdc_800_df.copy()
    test_df = data_btc_usdc_200_df.copy()

    model_params = dict(
        features=[mid.Candle(
            variation_length=3,
        )],
        sk_preproc="MinMaxScaler",
        sk_preproc_params={"feature_range": (0, 1)},
        params=dict(
            seed=56,
            seq_length=2,
            units=75,
            batch_size=10,
        ),
    )

    expected_results = dict(
        mae_train=0.000828552061262521,
        mae_test=0.0010543524386234248,
        acc_test=0.48148148148148145,
        ngp_test=13,
    )

    test_pm_gen(model_params=model_params,
                train_df=train_df,
                test_df=test_df,
                test_id=test_id,
                expected_results=expected_results,
                update_expect=update_expect)
