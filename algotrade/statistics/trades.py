import numpy as np
import pandas as pd
import os
import yaml
from tqdm import tqdm

class Trades(object):
    """
    统计每个标的物平均每天买入和卖出的数量, 以及平均交易金额，还手率
    """
    def __init__(self, account_path):
        self.account_path = account_path
        self.store_path = os.path.join(self.account_path, 'statistics', 'trades')
        print('[Statistics][Trades] init ...')


    def run(self):
        self.load_fill()
        self.cal_trades()
        self.cal_trades_amount()
        self.store_trades()
        self.store_trades_amount()


    def load_fill(self):
        self.fill_dict = {}
        file_path = os.path.join(self.account_path, 'fill', 'history_fill.yaml')
        with open(file_path, 'r') as f:
            history_fill_dict = yaml.load(f)
        for timestamp in history_fill_dict:
            self.fill_dict[timestamp] = pd.DataFrame(history_fill_dict[timestamp]).T
        #fill_dict[timestamp]['dates'] = timestamp[:10]


    def cal_trades(self):
        buy_trades_df = pd.DataFrame()
        sell_trades_df = pd.DataFrame()
        timestamp_list = []
        for timestamp in tqdm(self.fill_dict.keys()):
            self.fill_dict[timestamp]['buy_trades'] = (self.fill_dict[timestamp]['买卖方向'] == '买') * self.fill_dict[timestamp]['成交数量']
            self.fill_dict[timestamp]['sell_trades'] = (self.fill_dict[timestamp]['买卖方向'] == '卖') * self.fill_dict[timestamp]['成交数量']

            buy_trades_df = buy_trades_df.append(self.fill_dict[timestamp]['buy_trades'], ignore_index=True)
            sell_trades_df = sell_trades_df.append(self.fill_dict[timestamp]['sell_trades'], ignore_index=True)

            timestamp_list.append(timestamp[:10]+timestamp[10:].replace('-', ':'))

        buy_trades_df.index = pd.to_datetime(timestamp_list)
        sell_trades_df.index = pd.to_datetime(timestamp_list)
        self.daily_buy_trades = buy_trades_df.groupby([lambda x:x.year, lambda x:x.month, lambda x:x.day]).sum()
        self.daily_sell_trades = sell_trades_df.groupby([lambda x:x.year, lambda x:x.month, lambda x:x.day]).sum()

        self.daily_buy_trades.loc['average'] = self.daily_buy_trades.mean().astype('int32')
        self.daily_sell_trades.loc['average'] = self.daily_sell_trades.mean().astype('int32')



    def cal_trades_amount(self):
        """
        统计daily的成交金额
        """
        buy_trades_df = pd.DataFrame()
        sell_trades_df = pd.DataFrame()
        timestamp_list = []
        for timestamp in tqdm(self.fill_dict.keys()):
            self.fill_dict[timestamp]['buy_trades_amount'] = (self.fill_dict[timestamp]['买卖方向'] == '买') * self.fill_dict[timestamp]['成交额']
            self.fill_dict[timestamp]['sell_trades_amount'] = (self.fill_dict[timestamp]['买卖方向'] == '卖') * self.fill_dict[timestamp]['成交额']
            buy_trades_df = buy_trades_df.append(self.fill_dict[timestamp]['buy_trades_amount'], ignore_index=True)
            sell_trades_df = sell_trades_df.append(self.fill_dict[timestamp]['sell_trades_amount'], ignore_index=True)
            timestamp_list.append(timestamp[:10]+timestamp[10:].replace('-', ':'))
        buy_trades_df.index = pd.to_datetime(timestamp_list)
        sell_trades_df.index = pd.to_datetime(timestamp_list)
        self.daily_buy_trades_amount = buy_trades_df.groupby([lambda x:x.year, lambda x:x.month, lambda x:x.day]).sum()
        self.daily_sell_trades_amount = sell_trades_df.groupby([lambda x:x.year, lambda x:x.month, lambda x:x.day]).sum()

        self.daily_buy_trades_amount.loc['average'] = self.daily_buy_trades_amount.mean().astype('int32')
        self.daily_sell_trades_amount.loc['average'] = self.daily_sell_trades_amount.mean().astype('int32')

        

    def store_trades(self):
        """
        存储买入卖空数据
        """
        account_path = os.path.join(self.account_path, 'statistics')
        if not os.path.exists(account_path):
            os.mkdir(account_path)
        if not os.path.exists(self.store_path):
            os.mkdir(self.store_path)
        self.daily_buy_trades.to_csv(os.path.join(self.store_path, 'daily_buy_trades.csv'))
        self.daily_sell_trades.to_csv(os.path.join(self.store_path, 'daily_sell_trades.csv'))


    def store_trades_amount(self):
        """
        存储买入卖空数据
        """
        account_path = os.path.join(self.account_path, 'statistics')
        if not os.path.exists(account_path):
            os.mkdir(account_path)
        self.daily_buy_trades_amount.to_csv(os.path.join(self.store_path, 'daily_buy_trades_amount.csv'))
        self.daily_sell_trades_amount.to_csv(os.path.join(self.store_path, 'daily_sell_trades_amount.csv'))


