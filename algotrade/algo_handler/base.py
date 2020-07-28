from abc import ABCMeta, abstractmethod
from collections import deque, defaultdict
import numpy as np
import os
import pandas as pd

from ..utils.log import logger
from ..event import AlgoEvent
log = logger('[AlgoHandler]')



class AlgoHandler(object):
    def __init__(self, events_queue, subscribe_fields, look_back, store_path):
        self.tick_data = {}
        self.events_queue = events_queue
        self.subscribe_fields = subscribe_fields['TAQ'] + subscribe_fields['TRADE']
        self.look_back = look_back
        self.store_path = store_path
        self._init_TickFrame()
        self._init_history_algo()
        self._init_algo()

    def _init_TickFrame(self):
        for field in self.subscribe_fields:
            self.tick_data[field] = pd.DataFrame()
        self.tick_data['timeindex'] = []



    def _init_history_algo(self):
        self.history_algo_dict = {}
        self.history_predict_df = pd.DataFrame()


    def _init_algo(self):
        self.algo_id = 0


    def _update_timestamp(self, event):
        if self.is_tick_event(event):
            self.timestamp = event.timestamp
        return

    def _update_ticker_names(self, event):
        if self.is_tick_event(event):
            self.ticker_names = event.ticker_names
        return


    def _update_TickFrame(self, event):
        if self.is_tick_event(event):
            log.info('update TickFrame')
            self.tick_data['timeindex'].append(event.timestamp)

            for field in self.subscribe_fields:
                df = pd.DataFrame(event.field_dict[field], index=[event.timestamp])
                self.tick_data[field] = self.tick_data[field].append(df)
                setattr(self, field, self.tick_data[field].iloc[-self.look_back:].values)
                # print(field)
                # print(df)
            self.timeindex = self.tick_data['timeindex']
        return


    def _calculate_algo(self, event):
        if self.is_tick_event(event) and self.is_lookback_complete():
            log.info('calculate algo: %s' %self.algo_name)
            self.algo_dict = defaultdict(lambda:0)
            self.calculate_algo()
            #self.history_predict_df.append(self.predict)
        return



    def _update_event(self, event):
        if self.is_tick_event(event) and self.is_lookback_complete():
            algo_event = AlgoEvent(algo_name=self.algo_name, 
                                    timestamp=event.timestamp,
                                    algo = self.algo_dict)
            self.events_queue.put(algo_event)
        return 




    # 外部调用 ----------------------------------------------------------------------------
    def on_tick(self, event):
        self._update_timestamp(event)
        self._update_ticker_names(event)
        self._update_TickFrame(event)
        self._calculate_algo(event)
        self._update_event(event)
        #self.store()


    def store(self):
        if self.store_path is None: return
        store_path = os.path.join(self.store_path, 'algo')
        if not os.path.exists(store_path):
            os.mkdir(store_path)
        pd.DataFrame(self.history_algo_dict).to_csv(os.path.join(store_path, self.algo_name+'.csv'))
        #self.history_predict_df.to_csv(os.path.join(store_path, 'predict.csv'))
        return


    def is_tick_event(self, event):
        if event.event_type == "TICK": 
            return True
        else:
            return False

    def is_lookback_complete(self):
        if len(self.tick_data['timeindex']) >= self.look_back:
            return True
        else:
            return False

    # def is_lookback_tick_event(self, event):
    #     if self.is_tick_event() and event.tick_marker == 'LOOKBACK':
    #         return True
    #     else:
    #         return False


    # def is_trade_tick_event(self, event):
    #     if self.is_tick_event(event) and event.tick_marker != 'LOOKBACK':
    #         return True
    #     else:
    #         return False

    def algo_order(self, ticker, direction, offset, numbers):
        self.algo_id += 1
        self.history_algo_dict[self.algo_id] = {'id': str(self.algo_id),
                                '证券代码': ticker,
                                '买卖方向': direction,
                                '开平仓': offset,
                                '委托数量': numbers,
                                '委托日期':self.timestamp}

        if direction == '买':
            self.algo_dict[ticker] += numbers
        elif direction == '卖':
            self.algo_dict[ticker] -= numbers
        return self.algo_id



