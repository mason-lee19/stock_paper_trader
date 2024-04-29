import argparse
import pandas as pd
import neat
import pickle
import os
from alpaca.rest import REST

from utils import DataHandler, ApplyIndicators, Plotter

# Amount in dollars per trade
TRADE_AMOUNT = 10,000

class TradeSimulation:

    def __init__(self,apiConfig,ticker):
        self.df = pd.DataFrame()
        self.close_prices = pd.DataFrame()

        self.config = self.get_config()

        self.results = []

        self.ticker = ticker

        self.api = REST(key_id=apiConfig.api_key,
                        secret_key=apiConfig.api_secret,
                        base_url=apiConfig.base_url)

    def prepare_data(self,dataMgr) -> None:
        # Query data
        df = dataMgr.query_crypto_data()
        df = dataMgr.drop_cols(df)

        # Apply techincal analysis
        indMgr = ApplyIndicators()
        df = indMgr.apply_ta(df)

        # Normalize 
        cols_to_exclude = ['symbol','timestamp']
        excluded_columns_df = df[cols_to_exclude]

        

        cols_to_normalize = df.drop(cols_to_exclude,axis=1).columns
        
        normalized_data = df[cols_to_normalize].apply(dataMgr.normalize)

        df_normalize = pd.concat([excluded_columns_df,normalized_data],axis=1)

        df_normalize.dropna(inplace=True)

        self.df = df_normalize

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
        if self.df['signal'].iloc[-1] == 'Buy':
            self.place_buy_order()
        elif self.df['signal'].iloc[-1] == 'Sell':
            cur_position = self.pull_position
            if cur_position:
                self.place_sell_order(cur_position.qty)

    def place_buy_order(self) -> None:
        order = self.api.submit_order(
            symbol=self.ticker,
            qty=self.calculate_buy_quantity(),
            side='buy',
            type='market'
        )

    def place_sell_order(self,quantity) -> None:
        order = self.api.submit_order(
            symbol=self.ticker,
            qty=quantity,
            side='sell',
            type='market'
        )

    def pull_position(self):
        try:
            ticker_position = self.api.get_open_position(self.ticker)
            return ticker_position
        except:
            print(f'No position found for symbol: {self.ticker}')
            return None

    def calculate_buy_quantity(self):
        cur_price = self.df['open'].iloc[-1]
        return round(TRADE_AMOUNT / cur_price,1)
        


def main(args):
    # Get api key and secret
    dataMgr = DataHandler(requestConfig=args)

    # Pull and prepare data to be analyzed by model
    simu = TradeSimulation(dataMgr,args.stockTicker)
    simu.prepare_data(dataMgr)

    simu.run_model(args.model)

    simu.check_signal()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-s","--stockTicker",type=str,default=None,help="stock ticker")
    parser.add_argument("-d","--startDate",type=str,default="2020-01-01",help="start date")
    parser.add_argument("-m","--model",type=str,default="Models/ModelA.pickle",help="Models/ModelA.pickle")

    args = parser.parse_args()

    main(args)