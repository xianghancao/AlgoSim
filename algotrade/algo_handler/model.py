import numpy as np
import pandas as pd
import joblib
import numpy as np
import bottleneck as bn

from ..utils.log import logger
log = logger('[AlgoHandler][Model]')


def rank_m(x):
    x[np.isnan(x)] = 0
    return x - np.nansum(x, axis=1).reshape(x.shape[0],1)/500

def ts_rank_m(x, period):
#    res = np.zeros(x.shape) * np.nan
#    for ix in range(0, x.shape[0] - period + 1):
#        res[ix + period - 1] = (np.argsort(np.argsort(x[ix:ix + period], axis=0), axis=0)[-1] + 1) * 1. / period
#    res[np.isnan(x)] = np.nan
    res = bn.move_rank(x, period, min_count=1, axis=0)
    return res


def ts_sum_m(x, period):
    return pd.DataFrame(x).rolling(period).sum().values

def future_m(x, period=1):
    res = np.zeros(x.shape) * np.nan
    res[:-period] = x[period:]
    return res

def delay_m(x, period=1):
    res = np.zeros(x.shape) * np.nan
    res[period:] = x[:-period]
    return res


def diff_m(x, period):
    return x - delay_m(x, period)
    
class Model():
    def __init__(self):
        print('v0.0.1')


    def cal_X(self, BuyVolume01, SellVolume01, BuyPrice01, SellPrice01,
                    TotalBuyOrderVolume, TotalSellOrderVolume, ActiveBuy, ActiveSell,
                    WtAvgSellPrice, WtAvgBuyPrice, ticker_names, timeindex): 
        """
        计算特征矩阵X
        """
        feature_dict = {}
        self.f1 = (BuyVolume01 - SellVolume01)/(BuyVolume01 + SellVolume01)
        self.f2 = diff_m(rank_m(self.f1), 20)
        self.f3 = ts_rank_m(self.f1, 3)
        self.f4 = diff_m(rank_m(self.f1), 3)
        self.f5 = diff_m(self.f1, 3)
        self.f6 = (TotalBuyOrderVolume - TotalSellOrderVolume)/(TotalBuyOrderVolume + TotalSellOrderVolume)
        self.f7 = diff_m(self.f6, 10)
        self.f8 = diff_m(rank_m(self.f6), 10)
        self.f9 = ts_rank_m(self.f6, 20)

        BuyPrice01[BuyPrice01==0] =  SellPrice01[BuyPrice01==0] - 0.01
        SellPrice01[SellPrice01==0] =  BuyPrice01[SellPrice01==0] + 0.01
        mid_price = (BuyPrice01 + SellPrice01)/2
        ret_6 = mid_price/delay_m(mid_price, 2) -1
        ret_60 = mid_price/delay_m(mid_price,20)-1
        ret_120 = mid_price/delay_m(mid_price,40) -1

        self.f10 = ret_120
        self.f11 = rank_m(ret_120)
        self.f12 = rank_m(ret_60)
        self.f13 = ts_rank_m(ret_60, 20)
        self.f14 = ret_6
        self.f15 = rank_m(ret_6)
        self.f16 = ts_rank_m(ret_6, 40)
        
        active_bs_imbalance120 = (ts_sum_m(ActiveBuy, 40) - ts_sum_m(ActiveSell, 40))/(ts_sum_m(ActiveBuy, 40) + ts_sum_m(ActiveSell, 40))
        active_bs_imbalance60 = (ts_sum_m(ActiveBuy, 20) - ts_sum_m(ActiveSell, 20))/(ts_sum_m(ActiveBuy, 20) + ts_sum_m(ActiveSell, 20))
        active_bs_imbalance30 = (ts_sum_m(ActiveBuy, 10) - ts_sum_m(ActiveSell, 10))/(ts_sum_m(ActiveBuy, 10) + ts_sum_m(ActiveSell, 10))
        
        self.f17 = active_bs_imbalance120
        self.f18 = ts_rank_m(self.f17, 3)
        self.f19 = ts_rank_m(active_bs_imbalance60, 20)
        self.f20 = active_bs_imbalance30
        self.f21 = diff_m(self.f20, 10)
        self.f22 = ts_rank_m(self.f20, 20)
        self.f23 = diff_m(self.f20, 3)
        self.f24 = diff_m(rank_m(self.f20), 20)
        self.f25 = diff_m(rank_m(self.f20), 3)

        price_imbalance = (WtAvgSellPrice - mid_price)/(WtAvgSellPrice-WtAvgBuyPrice)
        self.f26 = diff_m(price_imbalance, 10)
        self.f27 = rank_m(price_imbalance)
        self.f28 = diff_m(rank_m(price_imbalance), 20)
        self.f29 = diff_m(price_imbalance, 3)


    def cal_y(self, BuyPrice01, SellPrice01):
        """
        计算特征矩阵X对应的y
        """
        mid_price = (BuyPrice01 + SellPrice01)/2
        self.y = future_m(mid_price, 60)/mid_price - 1


    def fit(self):
        """
        离线回测
        """
        Y = self.y.flatten('F')
        X = np.vstack((self.f1.flatten('F'), self.f2.flatten('F'), self.f3.flatten('F'), self.f4.flatten('F'),
                       self.f5.flatten('F'), self.f6.flatten('F'), self.f7.flatten('F'), self.f8.flatten('F'),
                       self.f9.flatten('F'), self.f10.flatten('F'), self.f11.flatten('F'), self.f12.flatten('F'),
                       self.f13.flatten('F'), self.f14.flatten('F'), self.f15.flatten('F'),
                       self.f28.flatten('F'), self.f29.flatten('F'))).T
        pd.DataFrame(X).fillna(0, inplace=True)
        pd.DataFrame(Y).fillna(0, inplace=True)
        X[np.isinf(X)] = 0
        Y[np.isinf(Y)] = 0

        import statsmodels.api as sm
        X = sm.add_constant(X)
        model = sm.OLS(Y,X)
        self.reg_model = model.fit()


    def predict(self):
        """
        在线预测
        """
        X = np.vstack((self.f1[-1], self.f2[-1], self.f3[-1], self.f4[-1], self.f5[-1], self.f6[-1], self.f7[-1], self.f8[-1], self.f9[-1], 
            self.f10[-1], self.f11[-1], self.f12[-1], self.f13[-1], self.f14[-1], self.f15[-1], self.f16[-1], self.f17[-1], self.f18[-1],
            self.f19[-1], self.f20[-1], self.f21[-1], self.f22[-1], self.f23[-1], self.f24[-1], self.f25[-1], self.f26[-1], self.f27[-1],
            self.f28[-1], self.f29[-1])).T

        pd.DataFrame(X).fillna(0, inplace=True)
        X[np.isinf(X)] = 0
        y = X*np.array([ 8.31264346e-04,  0, 8.96479941e-05,  6.82576828e-04, -7.85994274e-04,
        1.49442546e-04,  1.33546463e-02, -1.13962501e-02,  1.54540861e-04,
        1.44654527e-01, -1.72515318e-01,  6.33161738e-02,  0, 2.02167511e+00,
       -2.23140282e+00,  2.01106302e-04,  1.71409332e-04,  7.21477461e-05,
        9.53081738e-05,  2.77125044e-04, -1.04011687e-04,  1.25233311e-04,
        1.00856955e-03, -9.96475219e-05, -1.01525665e-03,  3.30604160e-03,
        3.35190917e-04,  7.75227626e-03,  1.32179441e-02])
        y = np.nansum(y, axis=1)
        return y


    def summary(self):
        return self.reg_model.summary()

        



