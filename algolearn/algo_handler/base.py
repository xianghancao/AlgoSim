from abc import ABCMeta, abstractmethod
from collections import defaultdict
import numpy as np
import os
import pandas as pd

from ..utils.log import logger
from ..event import AlgoEvent
log = logger('[AlgoHandler]')



class AlgoHandler(object):
    def __init__(self):
        self.algo_id = 0
        self.history_algo_dict = {}


    def algo_order(self, ticker, direction, offset, numbers, score, spread, buy_price, sell_price, net_position):
        self.algo_id += 1
        self.history_algo_dict[self.algo_id] = {'id': str(self.algo_id),
                                        '委托日期':self.timestamp,
                                '证券代码': ticker,
                                '买卖方向': direction,
                                '开平仓': offset,
                                '委托数量': numbers,
                                'score':score,
                                'spread':spread,
                                'buy_price':buy_price,
                                'sell_price': sell_price,
                                'net_position': net_position}

        if direction == '买':
            self.algo_dict[ticker] += numbers
        elif direction == '卖':
            self.algo_dict[ticker] -= numbers
        return self.algo_id


    def _init_algo(self):
        self.algo_dict = defaultdict(lambda:0)
        
        
    def _update_timestamp(self, event):
        self.timestamp = event.timestamp
        return
    
    def _update_ticker_names(self, event):
        self.ticker_names = event.ticker_names
        return

  
                
    def _update_event(self, event):
        log.info(len(self.algo_dict))
        algo_event = AlgoEvent(algo_name=self.algo_name, 
                                timestamp=event.timestamp,
                                algo = self.algo_dict)
        self.events_queue.put(algo_event)
        return 



    # 外部调用 ----------------------------------------------------------------------------
    def on_model(self, event):
        if event.event_type == 'MODEL':
            self._update_timestamp(event)
            self._update_ticker_names(event)
            self._init_algo()
            self._excute_algo(event)
            self._update_event(event)

            
    def store(self):
        log.info('store ...')
        store_path = os.path.join(self.store_path, 'algo')
        if not os.path.exists(store_path):
            os.mkdir(store_path)
        df = pd.DataFrame(self.history_algo_dict).T
        df.to_csv(os.path.join(store_path, 'algo.csv'))
        return