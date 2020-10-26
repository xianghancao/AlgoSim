import os
import numpy as np
import pandas as pd

from ..utils.log import logger
log = logger('[F1]')
from .operators import *
from .feature_base import FeatureBase
  
class Feature(FeatureBase):
    def __init__(self, store_path):
        self.name = 'f1'
        self.store_path = store_path
        
        
    def gen_feature(self, dataObj): 
        f1 = (dataObj.BuyVolume01 - dataObj.SellVolume01)/(dataObj.BuyVolume01 + dataObj.SellVolume01)
        log.info('gen_feature')
        return f1[-1]