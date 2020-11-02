import numpy as np
import scipy.stats as st

#----------------------------------------------------------------------
def sort_quintiles(signal_arr, bottom, up):
    # 排序选择
    not_nan_num = - np.sum(np.isnan(signal_arr)) + len(signal_arr)
    bottom_num = np.round(bottom/100. * not_nan_num).astype(np.int)  
    up_num = np.round(up/100. * not_nan_num).astype(np.int)            # 四舍五入, 然后进行类型转换 9.5 ---> 10. ---> 10
    rank_signal_arr = np.argsort(np.argsort(signal_arr)).astype(np.float) + 1                #这里加1
    #rank_signal_arr[np.isnan(signal_arr)] = np.nan
    res = np.ones_like(signal_arr)
    res[rank_signal_arr <= bottom_num] = 0
    res[rank_signal_arr > up_num] = 0
    res[np.isnan(rank_signal_arr)] = np.nan
    return res

#----------------------------------------------------------------------
def scale_one(signal_arr):
    # 
    signal_arr[np.isinf(signal_arr)] = np.nan
    scaled_signal_arr = (signal_arr/ (np.nansum(np.abs(signal_arr)) + 1e-20)).T
    return scaled_signal_arr

#----------------------------------------------------------------------
def stat_quintiles(scaled_wgts, quintiles_num):
    # 多分位测试
    if  quintiles_num == 10:
        quintiles_1 = sort_quintiles(scaled_wgts, 0, 10)
        quintiles_2 = sort_quintiles(scaled_wgts, 10, 20)
        quintiles_3 = sort_quintiles(scaled_wgts, 20, 30)
        quintiles_4 = sort_quintiles(scaled_wgts, 30, 40)
        quintiles_5 = sort_quintiles(scaled_wgts, 40, 50)
        quintiles_6 = sort_quintiles(scaled_wgts, 50, 60)
        quintiles_7 = sort_quintiles(scaled_wgts, 60, 70)
        quintiles_8 = sort_quintiles(scaled_wgts, 70, 80)
        quintiles_9 = sort_quintiles(scaled_wgts, 80, 90)
        quintiles_10 = sort_quintiles(scaled_wgts, 90, 100)
    elif quintiles_num == 5:
        """
        五分位测试
        多头值和空头值最大的20%， 20%-40%， 40%-60%，60-80%，80%-100%
        """
        quintiles_1 = sort_quintiles(scaled_wgts, 0, 20)
        quintiles_2 = sort_quintiles(scaled_wgts, 20, 40)
        quintiles_3 = sort_quintiles(scaled_wgts, 40, 60)
        quintiles_4 = sort_quintiles(scaled_wgts, 60, 80)
        quintiles_5 = sort_quintiles(scaled_wgts, 80, 100)

    elif quintiles_num == 4:
        """
        4分位测试
        多头值和空头值最大的25%， 25%-50%， 50%-75%, 75%-100%
        """
        quintiles_1 = sort_quintiles(scaled_wgts, 0, 2)
        quintiles_2 = sort_quintiles(scaled_wgts, 25, 50)
        quintiles_3 = sort_quintiles(scaled_wgts, 50, 75)
        quintiles_4 = sort_quintiles(scaled_wgts, 75, 100)

    elif quintiles_num == 3:
        """
        3分位测试
        多头值和空头值最大的33%， 33%-66%, 66%-100%
        """
        quintiles_1 = sort_quintiles(scaled_wgts, 0, 33)
        quintiles_2 = sort_quintiles(scaled_wgts, 33, 67)
        quintiles_3 = sort_quintiles(scaled_wgts, 67, 100)
    
    elif quintiles_num == 2:
        """
        2分位测试
        多头值和空头值最大的33%， 33%-66%, 66%-100%
        """
        quintiles_1 = sort_quintiles(scaled_wgts, 0, 50)
        quintiles_2 = sort_quintiles(scaled_wgts, 50, 100)

    else:
        raise Exception('')



def rank(x):
    """
    [Definition] 对x进行空头和多头的横截面排序, 
    [Category] 统计
    这里需要注意，不能分别对多头和空头进行排序，不然会出现不对称性
    """
    tmp_x = x.copy() 
    idx = np.sum(~np.isnan(tmp_x), axis=1) == 0  #某行全为nan值

    tmp_x[idx, :] = 0
    sz = np.sum(~np.isnan(x), axis=1)
    res = (st.mstats.rankdata(tmp_x, axis=1).T/sz.astype(float)).T
    res[np.isnan(x)] = np.nan
    return res

