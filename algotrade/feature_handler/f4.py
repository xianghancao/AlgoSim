import os
import numpy as np
import pandas as pd
from numba import jit

from ..utils.log import logger
from .operators import *
from .feature_base import FeatureBase


class Feature(FeatureBase):
    def __init__(self, store_path):
        self.name = 'f4'
        
        
    def gen_feature(self, dataObj): 
        f = (BuyVolume01 - SellVolume01)/(BuyVolume01 + SellVolume01)
        f = diff_m(rank_m(f), 3)
        return f[-1]