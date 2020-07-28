import os
import pandas as pd
import numpy as np
import shutil
from tqdm import tqdm

from ..event import TickEvent
from .base import AbstractTickPriceHandler
from ..utils.log import logger
log = logger('[SimTickHandler]')



class TickPriceHandler(AbstractTickPriceHandler):
    def __init__(self, csv_dir, events_queue, start_date, end_date, look_back, subscribe_tickers, subscribe_fields, store_path=None):
        log.info('%s start:%s end:%s' %(csv_dir, start_date, end_date))
        self.events_queue = events_queue
        self.csv_dir = csv_dir
        self.start_date = start_date
        self.end_date = end_date
        self.look_back = look_back
        self.store_path = store_path
        self.subscribe_tickers = subscribe_tickers
        self.subscribe_fields = subscribe_fields
        self.tick_data = {}
        self.tick_marker_dict = {}
        self.iteration_end = False

        self._subscribe_ticker()
        self._subscribe_fields()
        self._load_files()
        self._init_history_tick()
        self._process_tick()
        self._init_iterator()


    def _subscribe_ticker(self):
        if self.subscribe_tickers is not None:
            self.subscribe_tickers = list(self.subscribe_tickers)
        log.info('subscribe_ticker %s' %self.subscribe_tickers)
        return


    def _subscribe_fields(self):
        self.tick_data['ticker_names'] = []
        self.tick_data['timestamp'] = []
        for fields in self.subscribe_fields:
            self.tick_data[fields] = pd.DataFrame()


    def _load_files(self):
        for ticker in tqdm(self.subscribe_tickers):
            if ticker[0] == '6':
                exchange = 'SSEL2'
            else:
                exchange = 'SZSEL2'
            csv_dir = os.path.join(self.csv_dir, '%s/STOCK/TAQ/' %exchange)
            df = pd.read_csv(os.path.join(csv_dir, ticker+'.csv'), index_col='TradingTime')
            self.tick_data['ticker_names'].append(ticker)
            for fields in self.subscribe_fields:
                self.tick_data[fields][ticker] = df[fields]
        print(self.tick_data['ticker_names'])
        self.tick_data['timestamp'] = self.tick_data[fields].index.values



    def update_tick(self):
        self._update_iterator()
        if self.iteration_end: return
        self._update_last_timestamp(str(self.tick_data['timestamp'][self.iter_num]))
        self._update_ticker_names(self.tick_data['ticker_names'])
        self._update_buy_price(self.tick_data['BuyPrice01'][self.iter_num], self.tick_data['ticker_names'])
        self._update_sell_price(self.tick_data['SellPrice01'][self.iter_num], self.tick_data['ticker_names'])
        self._update_tick_marker()
        self._update_history_tick()
        self._update_event()


    def _update_event(self):
        subscribe_fields_dict = {}
        for i in self.subscribe_fields:
            subscribe_fields_dict[i] = self.tick_data[i][self.iter_num]
        tick_event = TickEvent(ticker_names=self.ticker_names,
                        timestamp=str(self.tick_data['timestamp'][self.iter_num]),
                        tick_marker = self.tick_marker,
                        subscribe_fields_dict = subscribe_fields_dict
                        )

        self.events_queue.put(tick_event)



    def _init_history_tick(self):
        self.history_tick_dict = {}
        for i in self.subscribe_fields:
            self.history_tick_dict[i] = pd.DataFrame()



    def _process_tick(self):
        # 处理nan值
        for i in self.tick_data.keys():
            if i in ['ticker_names', 'timestamp', 'tick_marker']:
                continue
            self.tick_data[i] = pd.DataFrame(self.tick_data[i]).fillna(method='ffill').values



    def _init_iterator(self):
        """
        迭代器，生成索引
        """
        self.iterator = (i for i in range(len(self.tick_data['timestamp'])))


    def _update_iterator(self):
        try:
            self.iter_num = next(self.iterator)
        except StopIteration as e:
            log.info('The end of iteration')
            self.iteration_end = True
            return


    def _update_sell_price(self, sell_price, ticker_names):
        self.sell_price_01 = pd.Series(sell_price, ticker_names).to_dict()
        return

    def _update_buy_price(self, buy_price, ticker_names):
        self.buy_price_01 = pd.Series(buy_price, ticker_names).to_dict()
        return
    
    def _update_last_timestamp(self, last_timestamp):
        self.last_timestamp = last_timestamp
        return


    def _update_ticker_names(self, ticker_names):
        self.ticker_names = ticker_names
        return


    def _update_tick_marker(self):
        if self.iter_num < self.look_back-1: 
            self.tick_marker = 'LOOKBACK'
        else:
            self.tick_marker = 'BACKTEST'
        self.tick_marker_dict.update({self.last_timestamp:self.tick_marker})
        return


    def _update_history_tick(self):
        #bid_vol_1
        for field in self.subscribe_fields:
            tick_series = pd.Series(self.tick_data[field][self.iter_num].tolist(),
                                         index=self.tick_data['ticker_names'])
            tick_series.name = self.tick_data['timestamp'][self.iter_num]
            self.history_tick_dict[field] = self.history_tick_dict[field].append(tick_series.T)



    def store(self):
        if self.store_path is None: return
        store_path = os.path.join(self.store_path, 'price')
        if not os.path.exists(store_path):
            os.mkdir(store_path)

        df = pd.Series(self.tick_marker_dict)
        df.name = 'tick_marker'
        pd.DataFrame(df).to_csv(os.path.join(store_path, 'tick_marker.csv'))
        
        for field in self.subscribe_fields:
            self.history_tick_dict[field].to_csv(os.path.join(store_path, '%s.csv' %field))




    # 外部调用 ----------------------------------------------------------------------------
    def get_buy_price_01(self):
        return self.buy_price_01

    def get_sell_price_01(self):
        return self.sell_price_01

    def get_last_timestamp(self):
        return self.last_timestamp

    def get_ticker_names(self):
        return self.ticker_names

    def is_iteration_end(self):
        return self.iteration_end

    def get_last_tick_marker(self):
        return self.tick_marker
