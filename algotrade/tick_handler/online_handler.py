import os, time, datetime, shutil, pdb
import pandas as pd
import numpy as np
from tqdm import tqdm
import collections
from fastprogress.fastprogress import progress_bar

from ..event import TickEvent
from .base import AbstractTickHandler
from ..utils.log import logger
from ..utils.load_files import multi_process_read_csv, batch_read_csv
log = logger('[OnlineTickHandler]')

from numba import jit


class OnlineTickHandler(AbstractTickHandler):
    def __init__(self, csv_dir, date, events_queue, subscribe_tickers, subscribe_fields, store_path=None):
        """
        读取本地tick数据，生成TickEvent，保存历史数据
        params:
            csv_dir - csv 数据路径
            date - 指定回测日期
            events_queue - 事件队列实力
            subscribe_tickers - 订阅股票
            subscribe_fields - 订阅字段
            store_path - 存储tick相关数据的路径
        """
        self.events_queue = events_queue
        self.date = date
        self.csv_dir = csv_dir
        self.store_path = store_path
        self.subscribe_tickers = subscribe_tickers
        self.subscribe_fields = subscribe_fields
        super().__init__(events_queue, subscribe_tickers, subscribe_fields)


        self._subscribe_ticker()
        self._init_ticker()
        self._init_history_tick()
        self._init_tick()

        # online 
        self._load_original_files()
        self._init_TRADE_TAQ()
        self._init_TAQ_TRADE_iterator()



    # ------------------------------------------------------------------------
    def _load_original_files(self):
        # TRADE
        TAQ_csv_dir_list, TRADE_csv_dir_list = [], []
        for ticker in self.subscribe_tickers:
            if ticker[0] == '6':
                exchange = 'SSEL2'
            else:
                exchange = 'SZSEL2'
            TAQ_dir = os.path.join(self.csv_dir, '%s/%s/STOCK/TAQ/%s.csv' %(self.date, exchange, ticker))
            TRADE_dir = os.path.join(self.csv_dir, '%s/%s/STOCK/TRADE/%s.csv' %(self.date, exchange, ticker))

            if os.path.exists(TAQ_dir) and os.path.exists(TRADE_dir):
                TAQ_csv_dir_list.append(TAQ_dir)
                TRADE_csv_dir_list.append(TRADE_dir)

        self.TAQ_dict = batch_read_csv(TAQ_csv_dir_list, method='ffill')
        self.TRADE_dict = batch_read_csv(TRADE_csv_dir_list, method='ffill')


    def _init_TRADE_TAQ(self):
        self.TRADE_df, self.TAQ_df = pd.DataFrame(), pd.DataFrame()
        for i in progress_bar(self.TAQ_dict):
            df= self.TAQ_dict[i]
            df = df[['Symbol', 'Market', 'BuyPrice01', 'SellPrice01', 'BuyVolume01', 'SellVolume01', 'TotalBuyOrderVolume',
                     'TotalSellOrderVolume', 'WtAvgSellPrice', 'WtAvgBuyPrice']]
            self.TAQ_df = self.TAQ_df.append(df)

        for i in progress_bar(self.TRADE_dict):
            df = self.TRADE_dict[i]
            self.TRADE_df = self.TRADE_df.append(df)

        self.TRADE_df = self.TRADE_df.sort_index()
        self.TAQ_df = self.TAQ_df.sort_index()

        start = datetime.datetime(year=int(self.date[:4]), month=int(self.date[4:6]), day=int(self.date[6:8]), hour=9, minute=30, second=0, microsecond=0)
        self.TRADE_df = self.TRADE_df.loc[self.TRADE_df.index.values>=start.strftime('%Y-%m-%d %H:%M:%S.000')]
        self.TAQ_df = self.TAQ_df.loc[self.TAQ_df.index.values>=start.strftime('%Y-%m-%d %H:%M:%S.000')]


    def _init_TAQ_TRADE_iterator(self):
        self.TAQ_iterator = (i for i in range(1, len(self.TAQ_df.index.values)))
        self.TRADE_iterator = (i for i in range(1, len(self.TRADE_df.index.values)))
        self.TAQ_iter_num = next(self.TAQ_iterator)
        self.TRADE_iter_num = next(self.TRADE_iterator)




    # ------------------------------------------------------------------------
    def _init_history_tick(self):
        """
        初始化tick记录
        """
        self.history_tick_dict = {}
        for i in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            self.history_tick_dict[i] = pd.DataFrame()



    # ------------------------------------------------------------------------
    def _init_TRADE_tick(self):
        for ticker in self.ticker_names:
            for field in self.subscribe_fields['TRADE']:
                self.tick_ticker_dict[ticker].update({field: 0})  #collections.defaultdict(lambda:0)




    # ------------------------------------------------------------------------
    def _update_tick(self):
        # TAQ
        while True:
            if self.TAQ_df.index.values[self.TAQ_iter_num] == self.timestamp:
                data = self.TAQ_df.iloc[self.TAQ_iter_num].to_dict()
                for field in self.subscribe_fields['TAQ']:
                    if data[field] != 0:
                        self.tick_ticker_dict[data['Symbol']][field] = float(data[field])
                    else:
                        continue
            elif self.TAQ_df.index.values[self.TAQ_iter_num] > self.timestamp:
                break
            self.TAQ_iter_num = next(self.TAQ_iterator)


        # TRADE
        while True:
            if self.TRADE_df.index.values[self.TRADE_iter_num] > self.previous_timestamp and \
                            self.TRADE_df.index.values[self.TRADE_iter_num] <= self.timestamp:
                data = self.TRADE_df.iloc[self.TRADE_iter_num].to_dict()
                if data['Market'] == 'SSE':
                    if data['BuySellFlag'] == 'B':
                        self.tick_ticker_dict[data['Symbol']]['ActiveBuy'] += float(data['TradeVolume'])
                    elif data['BuySellFlag'] == 'S':
                        self.tick_ticker_dict[data['Symbol']]['ActiveSell'] += float(data['TradeVolume'])
                elif data['Market'] == 'SZSE':
                    if data['BuyOrderID'] > data['SellOrderID'] and data['BuyOrderID'] != 0 and \
                                                                 data['SellOrderID'] != 0:
                        self.tick_ticker_dict[data['Symbol']]['ActiveBuy'] += float(data['TradeVolume'])
                    elif data['BuyOrderID'] < data['SellOrderID'] and data['BuyOrderID'] != 0 and \
                                                                 data['SellOrderID'] != 0:
                        self.tick_ticker_dict[data['Symbol']]['ActiveSell'] += float(data['TradeVolume'])

            elif self.TRADE_df.index.values[self.TRADE_iter_num] > self.timestamp:
                break
            self.TRADE_iter_num = next(self.TRADE_iterator)

        self.tick_field_dict = pd.DataFrame(self.tick_ticker_dict).T.to_dict()




    # ------------------------------------------------------------------------
    def _update_history_tick(self):
        for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            tick_series = pd.Series(self.tick_field_dict[field])
            tick_series.name = self.timestamp
            self.history_tick_dict[field] = self.history_tick_dict[field].append(tick_series.T)



    # 外部调用 ----------------------------------------------------------------------------
    def on_time(self, event):
        if event.event_type == 'TIME':
            self._update_timestamp(event)
            self._update_tick()     #online
            self._update_price()
            self._update_history_tick()  #online
            self._update_event()
            self._init_TRADE_tick()  #online



    def store(self):
        log.info('store ...')
        store_path = os.path.join(self.store_path, 'price')
        if not os.path.exists(store_path):
            os.mkdir(store_path)

        for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            self.history_tick_dict[field].to_csv(os.path.join(store_path, '%s.csv' %field))


