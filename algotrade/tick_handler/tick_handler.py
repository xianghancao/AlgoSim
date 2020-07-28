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
log = logger('[SimTickHandler]')



class TickHandler(AbstractTickHandler):
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

        self.iteration_end = False
        self.is_market_open = False

        self._subscribe_ticker()
        self._load_files()
        self._init_timeindex()
        self._init_ticker()
        self._init_iterator()
        self._init_history_tick()
        self._init_tick()



    # ------------------------------------------------------------------------
    def _subscribe_ticker(self): 
        """
        订阅股票
        """
        if self.subscribe_tickers is not None:
            self.subscribe_tickers = list(self.subscribe_tickers)
        log.info('subscribe_ticker %s' %self.subscribe_tickers)
        return



    # ------------------------------------------------------------------------
    def _load_files(self):
        # TRADE
        log.info('csv loading...')
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

            print(TAQ_dir)
        TAQ_dict = batch_read_csv(TAQ_csv_dir_list, method='ffill')
        TRADE_dict = batch_read_csv(TRADE_csv_dir_list, method='ffill')

        log.info('init TRADE, TAQ ...')
        self.TRADE_df, self.TAQ_df = pd.DataFrame(), pd.DataFrame()
        for i in progress_bar(TAQ_dict):
            df= TAQ_dict[i]
            df = df[['Symbol', 'Market', 'BuyPrice01', 'SellPrice01', 'BuyVolume01', 'SellVolume01', 'TotalBuyOrderVolume',
                     'TotalSellOrderVolume', 'WtAvgSellPrice', 'WtAvgBuyPrice']]
            self.TAQ_df = self.TAQ_df.append(df)

        for i in progress_bar(TRADE_dict):
            df = TRADE_dict[i]
            self.TRADE_df = self.TRADE_df.append(df)


        log.info('sort TRADE, TAQ timeindex...')
        self.TRADE_df = self.TRADE_df.sort_index()
        self.TAQ_df = self.TAQ_df.sort_index()


        start = datetime.datetime(year=int(self.date[:4]), month=int(self.date[4:6]), day=int(self.date[6:8]), hour=9, minute=30, second=0, microsecond=0)
        self.TRADE_df = self.TRADE_df.loc[self.TRADE_df.index.values>=start.strftime('%Y-%m-%d %H:%M:%S.000')]
        self.TAQ_df = self.TAQ_df.loc[self.TAQ_df.index.values>=start.strftime('%Y-%m-%d %H:%M:%S.000')]



    # ------------------------------------------------------------------------
    def _init_timeindex(self):
        """
        生成时间轴，3秒间隔的时间戳列表，负责全局迭代的索引
        """
        log.info('init timeindex...')

        delta = datetime.timedelta(days=0, seconds=3, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
        start = datetime.datetime(year=int(self.date[:4]), month=int(self.date[4:6]), day=int(self.date[6:8]), hour=9, minute=30, second=0, microsecond=0)
        self.timestamp_3s_list = []
        while True:
            self.timestamp_3s_list.append(start.strftime('%Y-%m-%d %H:%M:%S.000'))
            start = start+delta
            if start.hour >= 11 and start.minute >= 30: 
                break
            
        start = datetime.datetime(year=int(self.date[:4]), month=int(self.date[4:6]), day=int(self.date[6:8]), hour=13, minute=0, second=0, microsecond=0)
        while True:
            self.timestamp_3s_list.append(start.strftime('%Y-%m-%d %H:%M:%S.000'))
            start = start+delta
            if start.hour >= 14 and start.minute >= 55:
                break


    # ------------------------------------------------------------------------
    def _init_ticker(self):
        self.ticker_names = self.subscribe_tickers #np.unique(self.TAQ_df['Symbol'].values)



    # ------------------------------------------------------------------------
    def _init_iterator(self):
        """
        迭代器，生成索引
        """
        self.timestamp_3s_iterator = (i for i in range(1, len(self.timestamp_3s_list)))
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
    def _init_tick(self):
        """
        初始化tick_dict
        """
        self.tick_ticker_dict = {}
        for ticker in self.ticker_names:
            self.tick_ticker_dict[ticker] = {}
            for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
                self.tick_ticker_dict[ticker].update({field: 0})

    # ------------------------------------------------------------------------
    def _init_TRADE_tick(self):
        for ticker in self.ticker_names:
            for field in self.subscribe_fields['TRADE']:
                self.tick_ticker_dict[ticker].update({field: 0})  #collections.defaultdict(lambda:0)



    # ------------------------------------------------------------------------
    def _update_iterator(self):
        try:
            self.iter_num = next(self.timestamp_3s_iterator)
        except StopIteration as e:
            log.info('The end of iteration')
            self.iteration_end = True
            return

    # ------------------------------------------------------------------------
    def _is_market_open(self):
        t = time.strptime(self.timestamp_3s_list[self.iter_num], '%Y-%m-%d %H:%M:%S.000')
        if t.tm_hour == 9 and t.tm_min >= 30 and t.tm_sec>=0:
            self.is_market_open = True
        if t.tm_hour == 14 and t.tm_min >= 55:
            self.iteration_end = True
            self.is_market_open = False
            log.info('market end! 14:55:00')

    # ------------------------------------------------------------------------
    def _update_timestamp(self):
        self.timestamp = self.timestamp_3s_list[self.iter_num]
        self.previous_timestamp = self.timestamp_3s_list[self.iter_num-1]



    # ------------------------------------------------------------------------
    # 耗时大户 70s
    def _update_tick(self):
        # log.info('update tick ... previous_timestamp:%s timestamp:%s' %(self.previous_timestamp, self.timestamp))
        # TAQ
        while True:
            if self.TAQ_df.index.values[self.TAQ_iter_num] >= self.previous_timestamp and \
                            self.TAQ_df.index.values[self.TAQ_iter_num] < self.timestamp:
                data = self.TAQ_df.iloc[self.TAQ_iter_num].to_dict()
                for field in self.subscribe_fields['TAQ']:
                    if data[field] != 0:
                        self.tick_ticker_dict[data['Symbol']][field] = float(data[field])
                    else:
                        continue
            elif self.TAQ_df.index.values[self.TAQ_iter_num] >= self.timestamp:
                break
            self.TAQ_iter_num = next(self.TAQ_iterator)

        # TRADE
        while True:
            if self.TRADE_df.index.values[self.TRADE_iter_num] >= self.previous_timestamp and \
                            self.TRADE_df.index.values[self.TRADE_iter_num] < self.timestamp:
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

            elif self.TRADE_df.index.values[self.TRADE_iter_num] >= self.timestamp:
                break
            self.TRADE_iter_num = next(self.TRADE_iterator)

        self.tick_field_dict = pd.DataFrame(self.tick_ticker_dict).T.to_dict()



    # ------------------------------------------------------------------------
    def _update_event(self):
        """
        更新事件到队列
        """
        tick_event = TickEvent(timestamp=self.timestamp,
                            ticker_names=self.ticker_names,
                            field_dict=self.tick_field_dict)
        self.events_queue.put(tick_event)


    # ------------------------------------------------------------------------
    def _update_price(self):
        self.sell_price_01 = self.tick_field_dict['SellPrice01']
        self.buy_price_01 = self.tick_field_dict['BuyPrice01']
        return



    # ------------------------------------------------------------------------
    # 耗时大户
    def _update_history_tick(self):
        for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            tick_series = pd.Series(self.tick_field_dict[field])
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
        self._update_price()
        self._update_history_tick()
        self._update_event()
        self._init_TRADE_tick()


    def store(self):
        if self.store_path is None: return
        log.info('store in path:%s' %self.store_path)
        store_path = os.path.join(self.store_path, 'price')
        if not os.path.exists(store_path):
            os.mkdir(store_path)

        for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            self.history_tick_dict[field].to_csv(os.path.join(store_path, '%s.csv' %field))


    def get_all_timestamp(self):
        return self.timestamp_3s_list

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

