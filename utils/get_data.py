from dataclasses import dataclass

from alpaca.data import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame

import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

@dataclass
class ApiConfig:
    api_key: str
    api_secret: str
    base_url: str
    
class DataHandler:
    def __init__(self,requestConfig):
        self.apiConfig = self.configure_api()
        self.configure_crypto_client()
        self.reqConfig = requestConfig

    def configure_api(self) -> ApiConfig:
        local_dir = os.path.dirname(os.path.abspath('__file__'))
        parent_dir = os.path.dirname(local_dir)
        config_file_path = os.path.join(parent_dir,'API.env')
        load_dotenv(Path(config_file_path))

        config = ApiConfig(api_key=os.getenv("API_KEY"),
                           api_secret=os.getenv("API_SECRET"),
                           base_url=os.getenv("BASE_URL"))

        return config

    def configure_crypto_client(self) -> None:
        self.client = CryptoHistoricalDataClient(api_key=self.apiConfig.api_key,
                                                 secret_key=self.apiConfig.api_secret)

    def query_crypto_data(self) -> pd.DataFrame:
        request_params = CryptoBarsRequest(
            symbol_or_symbols=[self.reqConfig.stockTicker],
            timeframe=TimeFrame.Day,
            start=self.reqConfig.startDate
        )

        crypto_bars = self.client.get_crypto_bars(request_params=request_params)
        df = crypto_bars.df
        df.reset_index(inplace=True)

        return df

    def drop_cols(self,df:pd.DataFrame) -> pd.DataFrame:
        # Alpaca dataframe contains:
        # symbol | timestamp | open | high | low | close | volume | trade_count | vwap
        cols_list = df.columns
        if 'trade_count' in cols_list:
            df.drop(['trade_count'],axis=1,inplace=True)
        if 'vwap' in cols_list:
            df.drop(['vwap'],axis=1,inplace=True)

        return df

    def normalize(self,col):
        rolling_max = col.rolling(window=90, min_periods=30).max()
        rolling_min = col.rolling(window=90, min_periods=30).min()

        normalized_col = (col - rolling_min) / (rolling_max - rolling_min)

        return normalized_col

