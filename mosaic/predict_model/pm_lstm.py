import pydantic
import typing
import numpy as np
import random
import pandas as pd
try:
    import tensorflow as tf
    import tensorflow.keras as tfk

except ImportError:
    # Ce bloc est exécuté si TensorFlow ou Keras ne sont pas installés
    print("Please install tensorFlow : pip install tensorflow.")

from .pm_base import PMReturns
from ..utils.data_management import HyperParams

import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class LSTMParam(HyperParams):
    """
    Hyperparameters for the LSTM model.

    Attributes:
        seq_length (int): Sequence length to be considered
        units (int): Number of LSTM units.
        dropout (float): Dropout rate for regularization.
        recurrent_dropout (float): Recurrent dropout rate for regularization.
        epochs (int): Number of epochs for training.
        batch_size (int): Batch size for training.
    """
    seq_length: int = pydantic.Field(1, description="Sequence length of data to be fitted.")
    units: int = pydantic.Field(50, description="Number of LSTM units.")
    dropout: float = pydantic.Field(0.2, description="Dropout rate for regularization.")
    recurrent_dropout: float = pydantic.Field(0.2, description="Recurrent dropout rate for regularization.")
    epochs: int = pydantic.Field(100, description="Number of epochs for training.")
    batch_size: int = pydantic.Field(32, description="Batch size for training.")
    seed: int = pydantic.Field(None, description="Seed of the random generators")

class PMLSTM(PMReturns):
    """
    LSTM based predictive model for financial time series data.

    Inherits from PMReturns for handling financial data and adds LSTM model for prediction.

    Attributes:
        params (LSTMParam): Hyperparameters for the LSTM model.
    """
    params: LSTMParam = \
        pydantic.Field(LSTMParam(), description="LSTM hyper parameters")

    @property
    def bw_length(self):
        return super().bw_length + self.params.seq_length - 1

    def build_model(self, input_shape):
        """
        Builds the LSTM model based on the features DataFrame.

        Args:
            input_shape (tuple): Shape of input features.

        Returns:
            The instance itself.
        """
        if self.params.seed is not None:
            # NOTE: It seems required to set all these seeds
            # to ensure reproductibility (!)
            tf.random.set_seed(self.params.seed)
            np.random.seed(self.params.seed)
            random.seed(self.params.seed)

        self.bkd = tfk.models.Sequential()
        self.bkd.add(
            tfk.layers.LSTM(units=self.params.units,
                            input_shape=input_shape[1:],
                            # dropout=self.params.dropout,
                            # recurrent_dropout=self.params.recurrent_dropout,
                            return_sequences=True,
                            ))
        self.bkd.add(tfk.layers.Dropout(self.params.dropout))
        #ipdb.set_trace()

        self.bkd.add(tfk.layers.LSTM(self.params.units,
                                     return_sequences=False))
        
        self.bkd.add(tfk.layers.Dropout(self.params.dropout))
        
        self.bkd.add(tfk.layers.Dense(1))  # Output layer for regression

        self.bkd.compile(optimizer='adam', loss='mean_squared_error')


    def prepare_features(self, ohlcv_df, dropna=True):
        """
        Prepares and reshapes features for LSTM input.

        Args:
            ohlcv_df (DataFrame): OHLCV data for feature preparation.

        Returns:
            DataFrame: Reshaped features DataFrame.
        """
        features_df = super().prepare_features(ohlcv_df, dropna=dropna)
        return features_df

    
    def prepare_data_fit(self, ohlcv_df, dropna=True, **kwrds):
        """
        Prepares data for fitting the LSTM model, including reshaping.

        Args:
            ohlcv_df (DataFrame): OHLCV data for training.
            dropna (bool): Whether to drop NA values.

        Returns:
            tuple: Tuple of reshaped features and target arrays.
        """
        features_df, target_s = \
            super().prepare_data_fit(ohlcv_df,
                                     dropna=dropna, **kwrds)

        data_len = len(features_df)
        features_arr_list = []
        target_arr_list = []
        
        for i in range(data_len - self.params.seq_length + 1):
            features_cur_df = \
                features_df.iloc[i:(i + self.params.seq_length)]
            features_arr = features_cur_df.values
            # target_cur_s = target_s.iloc[i:i + self.params.seq_length]
            # features_seq_cur_df = \
            #     pd.concat([features_cur_df, target_cur_s],
            #               axis=1)
            # features_seq = features_seq_cur_df.values
            target_val = target_s.iloc[i + self.params.seq_length - 1]
            features_arr_list.append(features_arr)
            target_arr_list.append(target_val)

        features_arr = np.array(features_arr_list)
        target_arr = np.array(target_arr_list)

        return features_arr, target_arr


    def prepare_data_predict(self, ohlcv_df, dropna=True, **kwrds):
        """
        Prepares data for fitting the LSTM model, including reshaping.

        Args:
            ohlcv_df (DataFrame): OHLCV data for training.
            dropna (bool): Whether to drop NA values.

        Returns:
            tuple: Tuple of reshaped features and target arrays.
        """
        features_df = \
            super().prepare_data_predict(ohlcv_df,
                                         dropna=dropna, **kwrds)

        data_len = len(features_df)
        features_arr_list = []

        for i in range(data_len - self.params.seq_length + 1):
            features_cur_df = \
                features_df.iloc[i:(i + self.params.seq_length)]
            features_arr_list.append(features_cur_df.values)

        features_arr = np.array(features_arr_list)

        return features_arr


    def fit(self, ohlcv_df, **kwrds):
        """
        Trains the LSTM model on the provided OHLCV data.
       
        Args:
            ohlcv_df (DataFrame): OHLCV data for training.

        Returns:
            PMLSTM: The instance itself.
        """
        features_arr, target_arr = self.prepare_data_fit(ohlcv_df, **kwrds)

        self.build_model(features_arr.shape)
        self.bkd.fit(features_arr, target_arr,
                     epochs=self.params.epochs,
                     batch_size=self.params.batch_size)

        return self


    def predict(self, ohlcv_df, **kwrds):
        """
        Predicts using the trained LSTM model on the provided OHLCV data.

        Args:
            ohlcv_df (DataFrame): OHLCV data for prediction.

        Returns:
            Series: Predicted values.
        """
        features_arr = \
            self.prepare_data_predict(ohlcv_df, dropna=False, **kwrds)
        # features_arr = np.reshape(features_arr,
        #                           features_arr.shape[1:])

        #ipdb.set_trace()
        predictions_arr_raw = self.bkd.predict(features_arr)

        predictions_arr = self.postproc_data_predict(predictions_arr_raw)

        predictions_s = pd.Series(predictions_arr.flatten(),
                                  index=ohlcv_df.index[-len(predictions_arr):],
                                  name=self.var_target)

        return predictions_s

