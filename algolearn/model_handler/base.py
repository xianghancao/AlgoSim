import numpy as np
import pandas as pd


from ..utils.log import logger
log = logger('[ModelHandler]')

    
class ModelHandler():
    def __init__(self):
        pass

    def _update_timestamp(self, event):
        self.timestamp = event.timestamp
        
    def _update_ticker_names(self, event):
        self.ticker_names = event.ticker_names
        
        
    def store(self):
        pass


        




