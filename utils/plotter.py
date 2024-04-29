import matplotlib.pyplot as plt
from matplotlib.dates import date2num
import pandas as pd

class Plotter:
    def __init__(self,results,close_prices):
        self.df = close_prices

        self.buy_indices = [idx for action,idx in results if action=='BUY']
        self.buy_prices = [close_prices.iloc[idx] for idx in self.buy_indices]
        self.sell_indices = [idx for action,idx in results if action=='SELL']
        self.sell_prices = [close_prices.iloc[idx] for idx in self.sell_indices]

        self.plot()

    def plot(self):
        plt.plot(self.df['close'],label='close')

        plt.scatter(self.buy_indices,self.buy_prices,color="green",
                    marker='^',label='Buy')
        plt.scatter(self.sell_indices,self.sell_prices,color='red',
                    marker='v',label='Sell')
        
        plt.xlabel('Index')
        plt.ylabel('Price')

        plt.title(f'Model Signal BackTest, percent made: {self.calc_percent()} for {len(self.buy_indices)} trades')

        plt.legend()

        plt.show()

    def calc_percent(self) -> int:
        total_percent_change = 0

        for buy_price, sell_price in zip(self.buy_prices,self.sell_prices):
            percent_change = ((sell_price-buy_price)/buy_price) * 100
            total_percent_change += percent_change
        
        return total_percent_change