import os
import pandas as pd
import numpy as np
import shutil
from tqdm import tqdm
import time
import datetime
from fastprogress.fastprogress import progress_bar
import collections
import pdb

from ..event import TickEvent
from .base import AbstractTickHandler
from ..utils.log import logger
log = logger('[SimTickHandler]')



class TickHandler(AbstractTickHandler):
    def __init__(self, csv_dir, date, events_queue, subscribe_tickers, subscribe_fields, store_path=None):
        self.events_queue = events_queue
        self.date = date
        self.csv_dir = csv_dir
        #self.look_back = look_back
        self.store_path = store_path
        self.subscribe_tickers = subscribe_tickers
        self.subscribe_fields = subscribe_fields
        #self.tick_marker_dict = {}
        self.iteration_end = False
        self.is_market_open = False

        self._subscribe_ticker()
        self._load_files()
        self._init_timeindex()
        self._init_tick()
        self._init_history_tick()
        self._init_iterator()


    # ------------------------------------------------------------------------
    def _subscribe_ticker(self):
        if self.subscribe_tickers is not None:
            self.subscribe_tickers = list(self.subscribe_tickers)
        log.info('subscribe_ticker %s' %self.subscribe_tickers)
        return


    # ------------------------------------------------------------------------
    def _load_files(self):
        # TRADE
        log.info('TRADE loading...')
        self.TRADE_df, self.TAQ_df = pd.DataFrame(), pd.DataFrame()
        for ticker in progress_bar(self.subscribe_tickers):
            if ticker[0] == '6':
                exchange = 'SSEL2'
            else:
                exchange = 'SZSEL2'
            try:
                csv_dir = os.path.join(self.csv_dir, '%s/%s/STOCK/TRADE/' %(self.date, exchange))
                df = pd.read_csv(os.path.join(csv_dir, ticker+'.csv'), index_col='TradingTime')
                df['type'] = 'TRADE'
                df['exchange'] = exchange
                df['Symbol'] = ticker
                self.TRADE_df = self.TRADE_df.append(df)

            except FileNotFoundError:
                continue

        # TAQ
        log.info('TAQ loading...')
        for ticker in progress_bar(self.subscribe_tickers):
            if ticker[0] == '6':
                exchange = 'SSEL2'
            else:
                exchange = 'SZSEL2'
            try:
                csv_dir = os.path.join(self.csv_dir, '%s/%s/STOCK/TAQ/' %(self.date, exchange))
                df = pd.read_csv(os.path.join(csv_dir, ticker+'.csv'), index_col='TradingTime')
                df = df[['BuyPrice01', 'SellPrice01', 'BuyVolume01', 'SellVolume01', 'TotalBuyOrderVolume',
                         'TotalSellOrderVolume', 'WtAvgSellPrice', 'WtAvgBuyPrice']]
                df['type'] = 'TAQ'
                df['exchange'] = exchange
                df['Symbol'] = ticker
                self.TAQ_df = self.TAQ_df.append(df)

            except FileNotFoundError:
                continue

        self.TRADE_df = self.TRADE_df.sort_index()
        self.TAQ_df = self.TAQ_df.sort_index()

    # ------------------------------------------------------------------------
    def _init_timeindex(self):
        """
        生成时间轴，可用指定为TAQ的时间轴，可用可以用1s
        """

        delta = datetime.timedelta(days=0, seconds=3, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
        start = datetime.datetime(year=int(self.date[:4]), month=int(self.date[4:6]), day=int(self.date[6:8]), hour=9, minute=30, second=0, microsecond=0)
        self.timeindex = []
        while True:
            self.timeindex.append(start.strftime('%Y-%m-%d %H:%M:%S.000')) 
            start = start+delta
            if start.hour >= 14 and start.minute >= 55:
                break

    # ------------------------------------------------------------------------
    def _init_tick(self):
        self.tick_dict = {}
        for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            self.tick_dict[field] = collections.defaultdict(lambda:0)



    # ------------------------------------------------------------------------
    def _init_history_tick(self):
        """
        初始化tick记录
        """
        self.history_tick_dict = {}
        for i in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            self.history_tick_dict[i] = pd.DataFrame()



    # def _process_tick(self):
    #     # 处理nan值
    #     for i in self.tick_data.keys():
    #         if i in ['ticker_names', 'timestamp', 'tick_marker']:
    #             continue
    #         self.tick_data[i] = pd.DataFrame(self.tick_data[i]).fillna(method='ffill').fillna(0).values


    # ------------------------------------------------------------------------
    def _init_iterator(self):
        """
        迭代器，生成索引
        """
        self.iterator = (i for i in range(1, len(self.timeindex)))


    # ------------------------------------------------------------------------
    def _update_iterator(self):
        try:
            self.iter_num = next(self.iterator)
        except StopIteration as e:
            log.info('The end of iteration')
            self.iteration_end = True
            return

    # ------------------------------------------------------------------------
    def _is_market_open(self):
        t = time.strptime(self.timeindex[self.iter_num], '%Y-%m-%d %H:%M:%S.000')
        if t.tm_hour == 9 and t.tm_min >= 30 and t.tm_sec>=3:
            self.is_market_open = True
        if t.tm_hour == 14 and t.tm_min >= 55:
            self.iteration_end = True
            self.is_market_open = False
            log.info('market end! 14:55:00')

    # ------------------------------------------------------------------------
    def _update_timestamp(self):
        self.timestamp = self.timeindex[self.iter_num]
        self.previous_timestamp = self.timeindex[self.iter_num-1]


    # ------------------------------------------------------------------------
    def _update_tick(self):
        #print('start_time - end_time: %s - %s' %(self.previous_timestamp, self.timestamp))
        # TAQ
        TAQ_data = self.TAQ_df.loc[np.logical_and(self.TAQ_df.index.values>self.previous_timestamp, 
                                    self.TAQ_df.index.values<=self.timestamp)]
        for idx in range(TAQ_data.shape[0]):
            data = TAQ_data.iloc[idx].to_dict()
            #print(data)
            for field in self.subscribe_fields['TAQ']:
                self.tick_dict[field][data['Symbol']] = data[field]


        # TRADE
        TRADE_data = self.TRADE_df.loc[np.logical_and(self.TRADE_df.index.values>self.previous_timestamp, 
                                    self.TRADE_df.index.values<=self.timestamp)]

        for idx in range(TRADE_data.shape[0]):
            data = TRADE_data.iloc[idx].to_dict()
            if data['exchange'] == 'SSEL2':
                if data['BuySellFlag'] == 'B':
                    self.tick_dict['ActiveBuy'][data['Symbol']] += data['TradeVolume']
                elif data['BuySellFlag'] == 'S':
                    self.tick_dict['ActiveSell'][data['Symbol']] += data['TradeVolume']
            elif data['exchange'] == 'SZSEL2':
                if data['BuyOrderID'] > data['SellOrderID']:
                    self.tick_dict['ActiveBuy'][data['Symbol']] += data['TradeVolume']
                elif data['BuyOrderID'] < data['SellOrderID']:
                    self.tick_dict['ActiveSell'][data['Symbol']] += data['TradeVolume']
        return


    # ------------------------------------------------------------------------
    def _update_event(self):
        """
        更新事件到队列
        """
        df = pd.DataFrame(self.tick_dict).loc[self.subscribe_tickers]
        tick_dict = {}
        for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            tick_dict[field] = df[field].values

        tick_event = TickEvent(timestamp=self.timestamp,
                            tick_dict = tick_dict)
        self.events_queue.put(tick_event)


    # ------------------------------------------------------------------------
    def _update_sell_price(self):
        self.sell_price_01 = self.tick_dict['SellPrice01']
        return

    # ------------------------------------------------------------------------
    def _update_buy_price(self):
        self.buy_price_01 = self.tick_dict['BuyPrice01']
        return
    

    # ------------------------------------------------------------------------
    def _update_history_tick(self):
        for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            tick_series = pd.Series(self.tick_dict[field])
            tick_series.name = self.timestamp
            self.history_tick_dict[field] = self.history_tick_dict[field].append(tick_series.T)
            #print(self.history_tick_dict[field])



    # 外部调用 ----------------------------------------------------------------------------
    def update_tick(self):
        self._update_iterator()
        self._is_market_open()
        if self.iteration_end: return
        if not self.is_market_open: return
        self._update_timestamp()
        self._update_tick()
        self._update_buy_price()
        self._update_sell_price()
        self._update_history_tick()
        self._update_event()
        self._init_tick()


    def store(self):
        if self.store_path is None: return
        store_path = os.path.join(self.store_path, 'price')
        if not os.path.exists(store_path):
            os.mkdir(store_path)

        for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            self.history_tick_dict[field].to_csv(os.path.join(store_path, '%s.csv' %field))


    def get_all_timestamp(self):
        return self.timeindex

    def get_buy_price_01(self):
        return self.buy_price_01

    def get_sell_price_01(self):
        return self.sell_price_01

    def get_last_timestamp(self):
        return self.timestamp

    def get_ticker_names(self):
        return self.ticker_names

    def is_iteration_end(self):
        return self.iteration_end

    def is_market_open(self):
        return self.is_market_open

    # def get_last_tick_marker(self):
    #     return self.tick_marker

