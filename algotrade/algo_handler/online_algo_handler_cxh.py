import os
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
import datetime

from ..utils.log import logger
log = logger('[OnlineAlgoHandler]')

from .base import AlgoHandler
from ..event import AlgoEvent

class OnlineAlgoHandler(AlgoHandler):

    def __init__(self, events_queue, position_handler, tick_handler, store_path):
        self.algo_name = 'Algo_101'
        self.events_queue = events_queue
        self.store_path = store_path
        self.position_handler = position_handler
        self.tick_handler = tick_handler
        super().__init__()
        self.last_algo_buy_open = {}
        self.last_algo_sell_open = {}
    

    def _excute_algo(self, event):
        y = event.predict_y
        fees = 0.0015

        BuyPrice01 = pd.Series(self.tick_handler.get_buy_price_01())[self.ticker_names].values
        SellPrice01 = pd.Series(self.tick_handler.get_sell_price_01())[self.ticker_names].values
        SellVolume01 = pd.Series(self.tick_handler.get_sell_volume_01())[self.ticker_names].values
        BuyVolume01 = pd.Series(self.tick_handler.get_buy_volume_01())[self.ticker_names].values
        
        spread = (SellPrice01 - BuyPrice01)/BuyPrice01
        
        self.position = self.position_handler.get_position()

        for i in range(len(self.ticker_names)):
            ticker = self.ticker_names[i]
            score = y[i]
            # 建仓
            if score < 0 and -1 * score - spread[i] - fees - 0.00008 > 0 and spread[i]>0 and self.timestamp[-12:] != '14:54:47.000':
                self.algo_order(ticker=ticker, direction='卖', offset='开仓', numbers=min(int(BuyVolume01[i]/10), self.position[ticker]['持仓'], int(self.position[ticker]['上限']/10)), score=round(score,6), spread=round(spread[i],6), buy_price= BuyPrice01[i], sell_price=SellPrice01[i], net_position=self.position[ticker]['净开仓'])
                self.last_algo_sell_open[ticker] = {'开仓时间': self.timestamp}
                

            # 平仓
            elif score > 0 and score - spread[i]/2 - 0.0005  > 0 \
                and self.position[ticker]['净开仓'] < 0 \
                and spread[i]>0 and self.timestamp[-12:] != '14:54:47.000': #\
                #and pd.to_datetime(self.timestamp) - pd.to_datetime(self.last_algo_sell_open[ticker]['开仓时间']) > datetime.timedelta(seconds=240):
                self.algo_order(ticker=ticker, direction='买', offset='平仓', numbers=min(int(SellVolume01[i]/10), -self.position[ticker]['净开仓']), score=round(score,6), spread=round(spread[i],6), buy_price= BuyPrice01[i], sell_price=SellPrice01[i], net_position=self.position[ticker]['净开仓'])


        
            elif self.timestamp[-12:] == '14:54:57.000' and self.position[ticker]['净开仓'] < 0:
                print('[收盘平仓]%s:%s' %(ticker, max(0, -self.position[ticker]['净开仓'])))
                self.algo_order(ticker=ticker, direction='买', offset='平仓', numbers=max(0, -self.position[ticker]['净开仓']), score=np.nan, spread=round(spread[i],6), buy_price= BuyPrice01[i], sell_price=SellPrice01[i], net_position=self.position[ticker]['净开仓'])

                        
#             if score > 0 and score - spread[i] - fees + 0.0005 > 0 and spread[i]>0:
#                 self.algo_order(ticker=ticker, direction='买', offset='开仓', numbers=int(SellVolume01[i]/10), score=round(score,6), spread=round(spread[i],6), buy_price= BuyPrice01[i], sell_price=SellPrice01[i], net_position=self.position[ticker]['净开仓'])
#                 self.last_algo_buy_open[ticker] = {'开仓时间': self.timestamp}
                
    
#             if score < 0 and -1 * score - spread[i]/2 - 0.0005  > 0 \
#                 and self.position[ticker]['净开仓'] > 0 \
#                 and spread[i]>0: # \
#                 #and pd.to_datetime(self.timestamp) - pd.to_datetime(self.last_algo_buy_open[ticker]['开仓时间']) > datetime.timedelta(seconds=240):
#                 self.algo_order(ticker=ticker, direction='卖', offset='平仓', numbers=int(BuyVolume01[i]/10), score=round(score,6), spread=round(spread[i],6), buy_price= BuyPrice01[i], sell_price=SellPrice01[i], net_position=self.position[ticker]['净开仓'])



        

