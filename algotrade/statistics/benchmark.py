import numpy as np
import pandas as pd
import os


class Benchmark(object):
    """
    1. 计算等权持有股票持仓的收益和风险
    2，计算指定权重的收益和风险
    3. 给定收益序列，返回匹配投资组合（相同时间段和相同初始资金）的收益和风险
    """
    def __init__(self, account_path=None):
        self.account_path = account_path
        self.store_path = os.path.join(self.account_path, 'statistics', 'benchmark')
        print('[Statistics][Benchmark] init ...')

    def run(self):
        self.load_bar_close_price()
        self.cal_equal_wgts_returns()
        self.store_equal_wgts_returns()

    def load_bar_close_price(self):
        close_price_df = pd.read_csv(os.path.join(self.account_path, 'price', 'vwap.csv'), index_col=0)
        bar_marker = pd.read_csv(os.path.join(self.account_path, 'price', 'bar_marker.csv'), index_col=0)

        self.close_price = close_price_df.loc[np.in1d(close_price_df.index.values,
                                    bar_marker['bar_marker'].index.values[bar_marker['bar_marker'].values != 'LOOKBACK'])]



    def cal_equal_wgts_returns(self):
        """
        计算等权重收益率， 这个不是累计收益率
        """
        returns_ = self.close_price/self.close_price.shift(1) - 1
        returns_ = returns_.mean(skipna=True, axis=1)
        self.equal_wgts_returns = returns_.fillna(value=0)
        # self.equal_wgts_returns.name = 'equal_wgts_returns'
        # self.equal_wgts_returns.header = ['equal_wgts_returns']


    def store_equal_wgts_returns(self):
        """
        存储等权重收益率， 这个不是累计收益率
        """
        if not os.path.exists(os.path.join(self.account_path, 'statistics')):
            os.mkdir(os.path.join(self.account_path, 'statistics'))
        if not os.path.exists(self.store_path):
            os.mkdir(self.store_path)
        df = pd.DataFrame(self.equal_wgts_returns, columns=['equal_wgts_returns'])
        df.to_csv(os.path.join(self.store_path, 'equal_wgts_benchmark.csv'))
