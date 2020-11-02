import numpy as np
import pandas as pd
import bottleneck as bn
from numba import jit


def rank_m(x):
    x[np.isinf(x)] = np.nan
    x = pd.DataFrame(x).fillna(method='ffill').values
    return x - np.nanmean(x, axis=1).reshape(-1,1)



def ts_rank_m(x, period):
#    res = np.zeros(x.shape) * np.nan
#    for ix in range(0, x.shape[0] - period + 1):
#        res[ix + period - 1] = (np.argsort(np.argsort(x[ix:ix + period], axis=0), axis=0)[-1] + 1) * 1. / period
#    res[np.isnan(x)] = np.nan
    res = bn.move_rank(x, period, min_count=1, axis=0)
    return res


def ts_sum_m(x, period):
    return pd.DataFrame(x).rolling(period).sum().values

# def future_m(x, period=1):
#     res = np.zeros(x.shape) * np.nan
#     res[:-period] = x[period:]
#     return res

def delay_m(x, period=1):
    res = np.zeros(x.shape) * np.nan
    res[period:] = x[:-period]
    return res


def diff_m(x, period):
    return x - delay_m(x, period)
    

def div_m(x , y):
    res = x/y
    return pd.DataFrame(res).replace([np.inf, -np.inf], np.nan, inplace=True).values