
import time
import joblib
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from .base import AlgoHandler
from .model import Model


class Algo(AlgoHandler):

    def __init__(self, events_queue, position_handler, subscribe_fields, store_path):
        self.algo_name = 'Algo_101'
        self.look_back = 120
        self.position_handler = position_handler
        super().__init__(events_queue, subscribe_fields, self.look_back, store_path)
        self.reg_model = Model()


    def calculate_algo(self):
        X = self.reg_model.cal_X(self.BuyVolume01, self.SellVolume01, self.BuyPrice01, self.SellPrice01,
                    self.TotalBuyOrderVolume, self.TotalSellOrderVolume, self.ActiveBuy, self.ActiveSell,
                    self.WtAvgSellPrice, self.WtAvgBuyPrice, self.ticker_names, self.timeindex)
        y = self.reg_model.predict()
        self._excute_algo(y)


    def _excute_algo(self, y):
        m = 0.0005
        fees = 0.0015
        spread = (self.SellPrice01[-1] - self.BuyPrice01[-1])/self.BuyPrice01[-1]

        self.position = self.position_handler.get_position()
        for i in range(len(self.ticker_names)):
            ticker = self.ticker_names[i]
            print(y[i], spread[i]/2, m, fees)
            # 建仓
            if -1 * y[i] - spread[i]/2 + m - fees > 0:
                self.algo_order(ticker=ticker, direction='卖', offset='开仓', numbers=100)
            if y[i] - spread[i]/2 + m - fees > 0:
                self.algo_order(ticker=ticker, direction='买', offset='开仓', numbers=100)

            # 平仓
            if y[i] - spread[i]/2 - m > 0 and \
                self.position[ticker]['净开仓'] < 0:
                self.algo_order(ticker=ticker, direction='买', offset='平仓', numbers=100)

            if -1 * y[i] - spread[i]/2 - m > 0 and \
                self.position[ticker]['净开仓'] > 0:
                self.algo_order(ticker=ticker, direction='卖', offset='平仓', numbers=100)

