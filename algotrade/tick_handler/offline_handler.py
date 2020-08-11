import os, time, datetime, pdb
import pandas as pd
import numpy as np
from tqdm import tqdm
from functools import reduce

from ..event import TickEvent
from .base import AbstractTickHandler
from ..utils.log import logger
log = logger('[OfflineTickHandler]')




class OfflineTickHandler(AbstractTickHandler):
    def __init__(self, off_path, date, events_queue, subscribe_tickers, subscribe_fields):
        """
        读取本地tick数据，生成TickEvent，保存历史数据
        params:
            csv_dir - csv 数据路径
            date - 指定回测日期
            events_queue - 事件队列实力
            subscribe_tickers - 订阅股票
            subscribe_fields - 订阅字段
        """
        self.events_queue = events_queue
        self.off_path = off_path
        self.date = date
        self.subscribe_tickers = subscribe_tickers
        self.subscribe_fields = subscribe_fields
        super().__init__(events_queue, subscribe_tickers, subscribe_fields)
   
        self._load_local_files() # offline
        self._subscribe_ticker()
        self._init_ticker()
        self._init_tick()


    # ------------------------------------------------------------------------
    def _load_local_files(self):
        self.field_df = {}
        local_files_path = os.path.join(self.off_path, 'price')
        log.info('load offline files: %s' %local_files_path)
        for field in tqdm(self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']):
            self.field_df[field] = pd.read_csv(os.path.join(local_files_path, field+'.csv'), index_col=0)
        self.columns = reduce(np.intersect1d, (self.field_df[i].columns.values for i in self.field_df))
        for field in tqdm(self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']):
            self.field_df[field] = self.field_df[field][self.columns]
       
    # ------------------------------------------------------------------------
    def _init_tick(self):
        self.ticker_names = self.columns
        
        
    # ------------------------------------------------------------------------
    def _update_tick(self):
        self.tick_field_dict = {}
        for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
            self.tick_field_dict[field] = self.field_df[field].loc[self.timestamp].to_dict()



    # 外部调用 ----------------------------------------------------------------------------
    def on_time(self, event):
        if event.event_type == 'TIME':
            self._update_timestamp(event)
            self._update_tick()
            self._update_price()
            self._update_event()


    def store(self):
        pass
