import os
import numpy as np
import pandas as pd
#from numba import jit
import importlib

from ..utils.log import logger
log = logger('[OnlineFeatureHandler]')
from .operators import *
from .base import FeatureHandler
from ..event import FeatureEvent
    
class Object():
    pass


class OnlineFeatureHandler(FeatureHandler):
    def __init__(self, events_queue, subscribe_fields, feature_name_list, store_path):
        self.look_back = 50
        self.feature_name_list = feature_name_list
        self.store_path = store_path
        self.events_queue = events_queue
        self.subscribe_fields = subscribe_fields['TAQ'] + subscribe_fields['TRADE']
        self.tick_data_df = {}
        
        super().__init__()
        self._init_TickFrame()
        self._init_history_feature()
        self._init_feature()
        
    def _init_feature(self):
        """
        初始化特征文件
        """
        self.feature_obj_dict = {}
        for feature_name in self.feature_name_list:
            feature_obj = importlib.import_module('algotrade.feature_handler.%s' %feature_name)
            self.feature_obj_dict[feature_name] = feature_obj.Feature(self.store_path)
        return
    
    def _calculate_X(self): 
        """
        计算特征矩阵X
        """
        log.info('calculate_X ...')
        self.feature_dict = {}
        for feature_name in self.feature_name_list:
            self.feature_dict[feature_name] = self.feature_obj_dict[feature_name].gen_feature(self.tick_obj)
        return
        
        
    def _update_event(self, event):
        algo_event = FeatureEvent(timestamp=self.timestamp,
                                  ticker_names=self.ticker_names,
                                  feature_dict=self.feature_dict)
        self.events_queue.put(algo_event)
        return 
    
    

    def _init_TickFrame(self):
        self.tick_obj = Object()
        for field in self.subscribe_fields:
            self.tick_data_df[field] = pd.DataFrame()
        self.tick_data_df['timeindex'] = []
        return
        
    def _init_history_feature(self):
        self.history_feature = {}
        for i in range(1, 30):
            self.history_feature['f%s' %i] = pd.DataFrame()
        self.history_y = pd.DataFrame()
        return
    
    def _update_history_feature(self):
        for i in self.feature_dict:
            self.history_feature[i] = self.history_feature[i].append(pd.DataFrame(self.feature_dict[i],
                                                                                 index=self.ticker_names,
                                                                                 columns=[self.timestamp]).T)
        return
        
    
    def _update_TickFrame(self, event):
        log.info('update TickFrame')
        self.tick_data_df['timeindex'].append(event.timestamp)

        for field in self.subscribe_fields:
            df = pd.DataFrame(event.field_dict[field], index=[event.timestamp])
            self.tick_data_df[field] = self.tick_data_df[field].append(df)
            setattr(self.tick_obj, field, self.tick_data_df[field].iloc[-self.look_back:].values)
        self.timeindex = self.tick_data_df['timeindex']
        return


        
    # 外部调用 ----------------------------------------------------------------------------
    def on_tick(self, event):
        if event.event_type == "TICK": 
            self._update_timestamp(event)
            self._update_ticker_names(event)
            self._update_TickFrame(event)
            if len(self.timeindex) >= self.look_back:
                self._calculate_X()
                self._update_event(event)
                self._update_history_feature()
        return     
        

    def store(self):
        log.info('store ...')
        store_path = os.path.join(self.store_path, 'feature')
        if not os.path.exists(store_path):
            os.mkdir(store_path)
        for i in self.history_feature:
            self.history_feature[i].to_csv(os.path.join(store_path, '%s.csv' %i))