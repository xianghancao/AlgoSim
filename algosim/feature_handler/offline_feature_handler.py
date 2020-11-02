import os
import numpy as np
import pandas as pd
from numba import jit
from tqdm import tqdm

from ..utils.log import logger
log = logger('[OnlineFeatureHandler]')
from .operators import *
from .base import FeatureHandler
from ..event import FeatureEvent
    
class OfflineFeatureHandler(FeatureHandler):
    def __init__(self, events_queue, subscribe_fields, off_path):
        self.off_path = off_path
        self.events_queue = events_queue
        super().__init__()
        
        self.history_feature = {}
        for i in range(1, 30):
            self.history_feature['f%s' %i] = pd.DataFrame()
        self.load_X()
    
        
    def load_X(self): 
        self.feature_df = {}
        for i in tqdm(['f1', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 
            'f10', 'f11', 'f12', 'f14', 'f15', 'f16', 'f17', 'f18',
            'f19', 'f20', 'f21', 'f22', 'f23', 'f24', 'f25', 'f26', 'f27',
            'f28', 'f29']):
            if 'ipynb' in i: continue
            self.feature_df[i] = pd.read_csv(os.path.join(self.off_path, 'feature', i+'.csv'), index_col=0)
            self.ticker_names = self.feature_df[i].columns.values 
            self.timestamp_arr = self.feature_df[i].index.values.astype('str')
            #log.info('%s: %s' %(i, self.feature_df[ii].shape))


        
    # 外部调用 ----------------------------------------------------------------------------
    def on_time(self, event):
        if event.event_type == 'TIME' and event.timestamp in self.timestamp_arr:
            self._update_timestamp(event)
            self._update_event(event)        

            

    def _update_event(self, event):
        feature_dict = {}
        for i in self.feature_df:
            feature_dict[i] = self.feature_df[i].loc[event.timestamp]
        
        algo_event = FeatureEvent(timestamp=self.timestamp,
                                  ticker_names=self.ticker_names,
                                  feature_dict=feature_dict)
        self.events_queue.put(algo_event)
        return 


