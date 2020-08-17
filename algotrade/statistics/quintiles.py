# encoding: utf-8
import numpy as np
import pandas as pd
import os 
import matplotlib.pyplot as plt

def scale_one(x):
    #归一化处理
    x[np.isinf(x)] = np.nan
    res = (x.T / (np.nansum(np.abs(x), axis=1) + 1e-20)).T
    return res

def cal_net_alpha_pnl(commission, alpha, alpha_pnl):
    commission = 0
    alpha[np.isnan(alpha)] = 0
    #print(alpha)
    scaled_alpha = scale_one(alpha)
    #print(scaled_alpha)
    shift = np.zeros_like(scaled_alpha) * np.nan
    shift[1:] = scaled_alpha[:-1]
    alpha_turnover_arr = np.nansum(np.abs(scaled_alpha - shift), axis=1)
    alpha_cost = commission * alpha_turnover_arr
    net_alpha_pnl = alpha_pnl - alpha_cost
    return net_alpha_pnl


class Quintiles():
    def __init__(self, quintiles_num, store_path):
        self.store_path = store_path
        self.quintiles_num = quintiles_num
        print('[Quintiles] quintiles_num: %s' %self.quintiles_num)


    def load_y(self):
        y = pd.read_csv(os.path.join(self.store_path, 'model/predict_y.csv'), index_col=0)
        buy_price = pd.read_csv(os.path.join(self.store_path, "price/BuyPrice01.csv" ), index_col=0)
        sell_price = pd.read_csv(os.path.join(self.store_path, "price/SellPrice01.csv"), index_col=0)
        buy_price[buy_price==0] = np.nan
        sell_price[sell_price==0] = np.nan 
        buy_price = buy_price.fillna(method='ffill')
        sell_price = sell_price.fillna(method='ffill')
        
        timestamp_arr = buy_price.index.values
        time_index = np.intersect1d(timestamp_arr, y.index.values)
        self.resample_return = (sell_price/sell_price.shift(1)-1).loc[time_index].values
        self.alpha = y.loc[time_index].values
        
        
    def run(self):
        self.load_y()
        self.stat_quintiles()
        self.stat_quintiles_pnl()
        self.plot()


    def sort_quintiles(self, wgts, bottom, up):
        # 排序选择
        not_nan_num = - np.sum(np.isnan(wgts), axis=1) + wgts.shape[1]
        bottom_num = (np.round(bottom/100. * not_nan_num).astype(np.int) * np.ones_like(wgts).T).T   
        up_num = (np.round(up/100. * not_nan_num).astype(np.int) * np.ones_like(wgts).T).T               # 四舍五入, 然后进行类型转换 9.5 ---> 10. ---> 10
        rank_wgts = np.argsort(np.argsort(wgts, axis=1), axis=1).astype(np.float) + 1                #这里加1
        rank_wgts[np.isnan(wgts)] = np.nan
        res = np.ones_like(wgts)
        res[rank_wgts <= bottom_num] = 0
        res[rank_wgts > up_num] = 0
        res[np.isnan(wgts)] = np.nan
        return res



    #----------------------------------------------------------------------
    def stat_quintiles(self):
        """
        五分位测试
        多头值和空头值最大的20%， 20%-40%， 40%-60%，60-80%，80%-100%
        """
        if self.quintiles_num == 5:
            self.quintiles_1 = self.sort_quintiles(self.alpha, 0, 20)
            self.quintiles_2 = self.sort_quintiles(self.alpha, 20, 40)
            self.quintiles_3 = self.sort_quintiles(self.alpha, 40, 60)
            self.quintiles_4 = self.sort_quintiles(self.alpha, 60, 80)
            self.quintiles_5 = self.sort_quintiles(self.alpha, 80, 100)

        elif self.quintiles_num == 10:
            self.quintiles_1 = self.sort_quintiles(self.alpha, 0, 10)
            self.quintiles_2 = self.sort_quintiles(self.alpha, 10, 20)
            self.quintiles_3 = self.sort_quintiles(self.alpha, 20, 30)
            self.quintiles_4 = self.sort_quintiles(self.alpha, 30, 40)
            self.quintiles_5 = self.sort_quintiles(self.alpha, 40, 50)
            self.quintiles_6 = self.sort_quintiles(self.alpha, 50, 60)
            self.quintiles_7 = self.sort_quintiles(self.alpha, 60, 70)
            self.quintiles_8 = self.sort_quintiles(self.alpha, 70, 80)
            self.quintiles_9 = self.sort_quintiles(self.alpha, 80, 90)
            self.quintiles_10 = self.sort_quintiles(self.alpha, 90, 100)
            
    def stat_quintiles_pnl(self):

        """
        五分位测试
        多头值和空头值最大的20%， 20%-40%， 40%-60%，60-80%，80%-100%
        """
        if self.quintiles_num == 5:
            self.quintiles_1_return = scale_one(self.quintiles_1) * self.resample_return
            self.quintiles_2_return = scale_one(self.quintiles_2) * self.resample_return
            self.quintiles_3_return = scale_one(self.quintiles_3) * self.resample_return
            self.quintiles_4_return = scale_one(self.quintiles_4) * self.resample_return
            self.quintiles_5_return = scale_one(self.quintiles_5) * self.resample_return

            self.quintiles_1_pnl = np.nan_to_num(np.nansum(self.quintiles_1_return, axis=1)) 
            self.quintiles_2_pnl = np.nan_to_num(np.nansum(self.quintiles_2_return, axis=1)) 
            self.quintiles_3_pnl = np.nan_to_num(np.nansum(self.quintiles_3_return, axis=1)) 
            self.quintiles_4_pnl = np.nan_to_num(np.nansum(self.quintiles_4_return, axis=1))
            self.quintiles_5_pnl = np.nan_to_num(np.nansum(self.quintiles_5_return, axis=1)) 

    #             self.quintiles_1_net_pnl = cal_net_alpha_pnl(self.cfg['Commission'], self.quintiles_1, self.quintiles_1_pnl) 
    #             self.quintiles_2_net_pnl = cal_net_alpha_pnl(self.cfg['Commission'], self.quintiles_2, self.quintiles_2_pnl) 
    #             self.quintiles_3_net_pnl = cal_net_alpha_pnl(self.cfg['Commission'], self.quintiles_3, self.quintiles_3_pnl) 
    #             self.quintiles_4_net_pnl = cal_net_alpha_pnl(self.cfg['Commission'], self.quintiles_4, self.quintiles_4_pnl)
    #             self.quintiles_5_net_pnl = cal_net_alpha_pnl(self.cfg['Commission'], self.quintiles_5, self.quintiles_5_pnl) 
        elif self.quintiles_num == 10:
            self.quintiles_1_return = scale_one(self.quintiles_1) * self.resample_return
            self.quintiles_2_return = scale_one(self.quintiles_2) * self.resample_return
            self.quintiles_3_return = scale_one(self.quintiles_3) * self.resample_return
            self.quintiles_4_return = scale_one(self.quintiles_4) * self.resample_return
            self.quintiles_5_return = scale_one(self.quintiles_5) * self.resample_return
            self.quintiles_6_return = scale_one(self.quintiles_6) * self.resample_return
            self.quintiles_7_return = scale_one(self.quintiles_7) * self.resample_return
            self.quintiles_8_return = scale_one(self.quintiles_8) * self.resample_return
            self.quintiles_9_return = scale_one(self.quintiles_9) * self.resample_return
            self.quintiles_10_return = scale_one(self.quintiles_10) * self.resample_return

            self.quintiles_1_pnl = np.nan_to_num(np.nansum(self.quintiles_1_return, axis=1)) 
            self.quintiles_2_pnl = np.nan_to_num(np.nansum(self.quintiles_2_return, axis=1)) 
            self.quintiles_3_pnl = np.nan_to_num(np.nansum(self.quintiles_3_return, axis=1)) 
            self.quintiles_4_pnl = np.nan_to_num(np.nansum(self.quintiles_4_return, axis=1))
            self.quintiles_5_pnl = np.nan_to_num(np.nansum(self.quintiles_5_return, axis=1)) 
            self.quintiles_6_pnl = np.nan_to_num(np.nansum(self.quintiles_6_return, axis=1)) 
            self.quintiles_7_pnl = np.nan_to_num(np.nansum(self.quintiles_7_return, axis=1)) 
            self.quintiles_8_pnl = np.nan_to_num(np.nansum(self.quintiles_8_return, axis=1)) 
            self.quintiles_9_pnl = np.nan_to_num(np.nansum(self.quintiles_9_return, axis=1))
            self.quintiles_10_pnl = np.nan_to_num(np.nansum(self.quintiles_10_return, axis=1)) 


    def plot(self):
        figure = plt.figure(figsize=(15,10))
        for i in range(1, self.quintiles_num+1):
            q_pnl = getattr(self, 'quintiles_' + str(i) + '_pnl')
            tmp = np.zeros(len(q_pnl)+1)
            tmp[1:] = np.cumsum(q_pnl)
            signal_line = plt.plot(tmp, '-', linewidth=1, label='quintiles_' + str(i) + '_pnl')
        plt.legend()
        plt.show()