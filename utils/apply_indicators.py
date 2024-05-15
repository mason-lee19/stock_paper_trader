import pandas_ta as ta
import pandas as pd

class ApplyIndicators:

    def apply_ta(self,df:pd.DataFrame):
        df = self.apply_indicators(df)
        return df

    def apply_indicators(self,df:pd.DataFrame):
        self.indicators = Indicators(df)

        ### Apply Techincal Indicators to dataframe ###

        # Simple moving average
        self.indicators.sma_n(20)
        self.indicators.sma_n(50)

        # Exponential Moving Average
        self.indicators.ema_n(20)
        self.indicators.ema_n(50)

        # Relative Strength Index
        self.indicators.rsi_n(14)

        # Moving Average Convergence Divergence
        self.indicators.macd()

        # Bollinger Bands
        self.indicators.bbands()

        # Average True Range
        self.indicators.atr_n(14)

        # On-Balance Volume
        self.indicators.obv()

        # Accumulation/Distribution Line
        self.indicators.adl()

        ### -------------------------------------- ###

        return self.indicators.df
        

class Indicators():
    def __init__(self,df:pd.DataFrame):
        self.df = df

    def sma_n(self,time_period:int=20):
        column_name = 'SMA_' + str(time_period)
        self.df[column_name] = ta.sma(self.df['close'], length=time_period)
    
    def ema_n(self,time_period:int=20):
        column_name = 'EMA_' + str(time_period)
        self.df[column_name] = ta.ema(self.df['close'], length=time_period)

    def rsi_n(self,time_period:int=14):
        column_name = 'RSI_' + str(time_period)
        self.df[column_name] = ta.rsi(self.df['close'], length=time_period)

    def macd(self):
        macd = ta.macd(self.df['close'],length=20)
        self.df['MACD'] = macd['MACD_12_26_9']
        self.df['MACD_Signal'] = macd['MACDs_12_26_9']

    def bbands(self):
        bbands = ta.bbands(self.df['close'],length=20)
        self.df['BB_Upper'] = bbands['BBU_20_2.0']
        self.df['BB_Middle'] = bbands['BBM_20_2.0']
        self.df['BB_Lower'] = bbands['BBL_20_2.0']

    def stoch_osci(self):
        stoch = ta.stoch(self.df['high'],self.df['low'], self.df['close'])
        self.df['Stoch_Oscil_K'] = stoch['STOCHk_14_3_3']
        self.df['Stoch_Oscil_D'] = stoch['STOCHd_14_3_3']

    def atr_n(self,time_period:int=14):
        column_name = 'ATR_' + str(time_period)
        self.df[column_name] = ta.atr(self.df['high'], self.df['low'], self.df['close'], timeperiod=time_period)

    def obv(self):
        self.df['OBV'] = ta.obv(self.df['close'], self.df['volume'])

    def adl(self):
        self.df['ADL'] = ta.ad(self.df['high'], self.df['low'], self.df['close'], self.df['volume'])

    def vwap(self):
        self.df['VWAP'] = ta.vwap(self.df['high'], self.df['low'], self.df['close'], self.df['volume'])

    def eom_n(self,time_period:int=14):
        column_name = 'EOM_' + str(time_period)
        self.df[column_name] = ta.eom(self.df['high'], self.df['low'], self.df['volume'], timeperiod=time_period)
    