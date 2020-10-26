import os
import numpy as np
import pandas as pd
from numba import jit

from ..utils.log import logger
log = logger('[F1]')
from .operators import *
from .feature_base import FeatureBase


class Feature(FeatureBase):
    def __init__(self, store_path):
        self.name = 'f3'
        
        
    def gen_feature(self, dataObj): 
        log.info('gen_feature')
        f = (dataObj.BuyVolume01 - dataObj.SellVolume01)/(dataObj.BuyVolume01 + dataObj.SellVolume01)
        f = ts_rank_m(f, 3)
        return f[-1]