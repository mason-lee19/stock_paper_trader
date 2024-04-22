import argparse
import pandas as pd
import neat
import pickle
import os

from utils import DataHandler, ApplyIndicators, Plotter

class TradeSimulation:

    def __init__(self):
        self.df = pd.DataFrame()
        self.close_prices = pd.DataFrame()

        self.config = self.get_config()

        self.results = []

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

        self.close_prices = df['close']

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


    def test_model(self,model_name):
        with open(model_name,"rb") as f:
            winner = pickle.load(f)
        winner_net = neat.nn.FeedForwardNetwork.create(winner,self.config)

        self.trade(winner_net)

    def trade(self,net):
        start_index = 30
        buy_signal = False

        for idx in range(start_index,len(self.df)):
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
                self.results.append(('BUY',idx))
            elif decision == 1 and buy_signal:
                buy_signal = False
                self.results.append(('SELL',idx))

def main(args):
    # Get api key and secret
    dataMgr = DataHandler(requestConfig=args)

    # Pull and prepare data to be analyzed by model
    simu = TradeSimulation()
    simu.prepare_data(dataMgr)

    simu.test_model(args.model)

    plot = Plotter(simu.results,simu.close_prices)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-s","--stockTicker",type=str,default=None,help="stock ticker")
    parser.add_argument("-d","--startDate",type=str,default="2020-01-01",help="start date")
    parser.add_argument("-m","--model",type=str,default="Models/ModelA.pickle",help="Models/ModelA.pickle")

    args = parser.parse_args()

    main(args)