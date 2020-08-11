import os
import numpy as np
import pandas as pd


from .base import ModelHandler
from ..event import ModelEvent
from ..utils.log import logger
log = logger('[OfflineModelHandler]')

    
class OfflineModelHandler(ModelHandler):
    def __init__(self, events_queue, off_path):
        print('v0.0.1')
        self.off_path = off_path
        self.events_queue = events_queue
        super().__init__()
        self.load_model()

        
    def load_model(self):
        df = pd.read_csv(os.path.join(self.off_path, 'model', 'predict_y.csv'), index_col=0)
        self.timestamp_arr = df.index.values.astype('str')
        self.predict_y = df
        self.ticker_names = df.columns.values
        return
    
    
    def update_event(self):
#         import pdb
#         pdb.set_trace()
        model_event = ModelEvent(timestamp=self.timestamp,
                                  ticker_names=self.ticker_names,
                                  predict_y=self.predict_y.loc[self.timestamp].values)
        self.events_queue.put(model_event)
        return
        
    


    def on_time(self, event):
        if event.event_type == 'TIME' and event.timestamp in self.timestamp_arr:
            self._update_timestamp(event)
            self.update_event()
            return
        
    def store(self):
        pass




