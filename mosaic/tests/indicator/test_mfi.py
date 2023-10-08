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


# =============== Tests begin here ================== #


def test_mfi_001():

    indic = mid.MFI()


def test_mfi_002(data_btc_usdc_20_df):

    indic = mid.MFI()

    assert indic.names() == [f'MFI_{indic.length}']

    indic_df = indic.compute(data_btc_usdc_20_df)
    assert isinstance(indic_df, pd.DataFrame)


def test_mfi_003(data_btc_usdc_20_df):

    indic = mid.MFI(length=1)

    assert indic.names() == ['MFI_1']

    indic_df = indic.compute(data_btc_usdc_20_df)

    assert isinstance(indic_df, pd.DataFrame)


def test_mfi_004(data_btc_usdc_20_df):

    indic = mid.MFI(length=2)

    assert indic.names() == ['MFI_2']

