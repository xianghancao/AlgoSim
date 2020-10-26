import numpy as np
import pandas as pd
import joblib
import numpy as np
import bottleneck as bn
from numba import jit

from ..utils.log import logger
log = logger('[FeatureHandler]')


class FeatureHandler(object):
    def __init__(self):
        pass

    def _update_timestamp(self, event):
        self.timestamp = event.timestamp
        return

    def _update_ticker_names(self, event):
        self.ticker_names = event.ticker_names
        return



        





