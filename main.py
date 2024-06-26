import pandas as pd
import neat
import pickle
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from utils import DataHandler, ApplyIndicators, DataBaseHandler, DataBaseConfig

# Amount in dollars per trade
TRADE_AMOUNT = 10000

class TradeSimulation:

    def __init__(self,apiMgr,ticker):
        self.df = pd.DataFrame()
        self.close_prices = pd.DataFrame()

        self.config = self.get_config()

        self.results = []

        self.ticker = ticker

        self.trading_client = TradingClient(apiMgr.apiConfig.api_key,
                                            apiMgr.apiConfig.api_secret,
                                            paper=True)

    def prepare_data(self,dataMgr) -> None:
        # Query data
        df = dataMgr.query_crypto_data()
        df = dataMgr.drop_cols(df)

        # Apply techincal analysis
        indMgr = ApplyIndicators()
        df = indMgr.apply_ta(df)

        # Save original data for results appending
        self.original_df = df

        # Normalize 
        cols_to_exclude = ['symbol','timestamp']
        excluded_columns_df = df[cols_to_exclude]

        cols_to_normalize = df.drop(cols_to_exclude,axis=1).columns
        
        normalized_data = df[cols_to_normalize].apply(dataMgr.normalize)

        df_normalize = pd.concat([excluded_columns_df,normalized_data],axis=1)

        df_normalize.dropna(inplace=True)

        self.df = df_normalize

    def prepare_db(self):
        db_config = DataBaseConfig(
            table_name='results',
            url='sqlite:///temp_db_file.db',
            bucket_name='trade-result-bucket',
            blob_name='trade-results.db'
        )

        self.db_handler = DataBaseHandler(db_config)

    def upload_results(self,trade_results:pd.DataFrame()):

        self.db_handler.push_to_db(trade_results)

        self.db_handler.upload_blob()
        

    def get_config(self):
        local_dir = os.path.dirname(__file__)
        config_path = os.path.join(local_dir,'config.txt')

        config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction, 
                            neat.DefaultSpeciesSet, neat.DefaultReproduction, config_path)

        return config


    def run_model(self,model_name):
        with open(model_name,"rb") as f:
            winner = pickle.load(f)
        winner_net = neat.nn.FeedForwardNetwork.create(winner,self.config)

        self.trade(winner_net)

    def trade(self,net):
        buy_signal = False

        for idx in range(len(self.df)):
            inputs = (buy_signal,
                      self.df['open'].iloc[idx],
                      self.df['high'].iloc[idx],
                      self.df['low'].iloc[idx],
                      self.df['close'].iloc[idx],
                      self.df['volume'].iloc[idx],
                      self.df['SMA_20'].iloc[idx],
                      self.df['SMA_50'].iloc[idx],
                      self.df['EMA_20'].iloc[idx],
                      self.df['RSI_14'].iloc[idx],
                      self.df['MACD'].iloc[idx],
                      self.df['MACD_Signal'].iloc[idx],
                      self.df['BB_Upper'].iloc[idx],
                      self.df['BB_Middle'].iloc[idx],
                      self.df['BB_Lower'].iloc[idx],
                      self.df['ATR_14'].iloc[idx],
                      self.df['OBV'].iloc[idx],
                      self.df['ADL'].iloc[idx])
            
            output = net.activate(inputs)
            decision = output.index(max(output))

            if decision == 0 and not buy_signal:
                buy_signal = True
                self.df.at[idx,'signal'] = 'Buy'
            elif decision == 1 and buy_signal:
                buy_signal = False
                self.df.at[idx,'signal'] = 'Sell'
            else:
                self.df.at[idx,'signal'] = None

    def check_signal(self):
        new_signal = False
        
        if self.df['signal'].iloc[-1] == 'Buy':
            self.place_buy_order()
            new_signal = True
        elif self.df['signal'].iloc[-1] == 'Sell':
            cur_position = self.pull_position()
            if cur_position:
                self.place_sell_order(cur_position.qty)
                new_signal = True
        else:
            print('No signal detected for today...')

        if new_signal:
            results = {'stock':[self.ticker],
                       'action':[self.df['signal'].iloc[-1]],
                       'price':[self.original_df['open'].iloc[-1]],
                       'date':[self.original_df['timestamp'].iloc[-1]]
            }
            self.prepare_db()
            self.upload_results(pd.DataFrame(results))

    def place_buy_order(self) -> None:
        market_order_data = MarketOrderRequest(
                            symbol=self.ticker,
                            qty=self.calculate_buy_quantity(),
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.GTC
        )
        
        market_order = self.trading_client.submit_order(
                       order_data=market_order_data
        )

    def place_sell_order(self,quantity) -> None:
        market_order_data = MarketOrderRequest(
                            symbol=self.ticker,
                            qty=quantity,
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.GTC
        )
        
        market_order = self.trading_client.submit_order(
                       order_data=market_order_data
        )

    def pull_position(self):
        try:
            if self.ticker == 'BTC/USD':
                ticker_position = self.trading_client.get_open_position('BTCUSD')
            return ticker_position
        except:
            print(f'No position found for symbol: {self.ticker}')
            return None

    def calculate_buy_quantity(self):
        cur_price = self.original_df['open'].iloc[-1]
        return round(TRADE_AMOUNT / int(cur_price),1)
        

def main(data,context):
    """
    Triggered from a messsage from Pub/Sub topic.
    """
    ticker = 'BTC/USD'
    startDate = '2023-01-01'
    model = "Models/ModelE.pickle"
    # Get api key and secret
    apiMgr = DataHandler(ticker,startDate)

    # Pull and prepare data to be analyzed by model
    simu = TradeSimulation(apiMgr,ticker)
    simu.prepare_data(apiMgr)

    simu.run_model(model)

    simu.check_signal()


if __name__ == "__main__":
    main()