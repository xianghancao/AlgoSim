# encoding: UTF-8

from enum import Enum
import numpy as np
import pandas as pd


class Event(object):
    """
    为继承事件提供接口
    """
    @property
    def typename(self):
        return self.event_type


#-----------------------------------------------------------------------------------------
class TimeEvent(Event):
    """
    行情生成此类事件，交由生成K线的算法处理，或者直接交由信号文件处理
    """
    def __init__(self, timestamp, previous_timestamp):
        """
        timestamp - The timestamp of the tick e.g. yyyy-mm-dd hh:mm:ss.mmm
        """
        self.event_type = "TIME"
        self.timestamp = timestamp
        self.previous_timestamp = previous_timestamp

    def __str__(self):
        return "[TimeEvent] %s" %str(self.timestamp) 



    
#-----------------------------------------------------------------------------------------
class TickEvent(Event):
    """
    行情生成此类事件，交由生成K线的算法处理，或者直接交由信号文件处理
    """
    def __init__(self, timestamp, ticker_names, field_dict):
        """
        Initialises the TickEvent.

        Parameters:
        ticker_names - [symbol1, symbol2, ...]
        timestamp - The timestamp of the tick e.g. yyyy-mm-dd hh:mm:ss.mmm
        """
        self.event_type = "TICK"
        self.timestamp = timestamp
        self.ticker_names = ticker_names
        self.field_dict = field_dict
        # for i in field_dict:
        #     setattr(self, i, field_dict[i])


    def __str__(self):
        return "[TickEvent] %s" %str(self.timestamp) 


    
#-----------------------------------------------------------------------------------------
class FeatureEvent(Event):
    """
    生成包含特征X和y的事件，交由ModelHandler处理
    """
    def __init__(self, timestamp, ticker_names, feature_dict):
        """
        Initialises the FeatureEvent.

        Parameters:
        ticker_names - [symbol1, symbol2, ...]
        timestamp - The timestamp of the tick e.g. yyyy-mm-dd hh:mm:ss.mmm
        """
        self.event_type = "FEATURE"
        self.timestamp = timestamp
        self.ticker_names = ticker_names
        self.feature_dict = feature_dict
        
    def __str__(self):
        return "[FeatureEvent] %s X nums:%s" %(self.timestamp, len(self.feature_dict))


                                                 
                                                 

#-----------------------------------------------------------------------------------------
class ModelEvent(Event):
    """
    生成predict_y的事件，交由AlgoHandler处理
    """
    def __init__(self, timestamp, ticker_names, predict_y):
        """
        Initialises the FeatureEvent.

        Parameters:
        ticker_names - [symbol1, symbol2, ...]
        timestamp - The timestamp of the tick e.g. yyyy-mm-dd hh:mm:ss.mmm
        """
        self.event_type = "MODEL"
        self.timestamp = timestamp
        self.ticker_names = ticker_names
        self.predict_y = predict_y
        
    def __str__(self):
        return "[ModelEvent] %s" %(self.timestamp)







#-----------------------------------------------------------------------------------------
class AlgoEvent(Event):
    """
    算法文件生成此类事件，交由Order model处理
    """
    
    def __init__(self, algo_name, timestamp, algo):
        self.event_type = "ALGO"
        self.algo_name = algo_name
        self.algo = algo
        self.timestamp = timestamp
        self._check()

    def __str__(self):
        return "[AlgoEvent] %s %s" %(self.algo_name, self.timestamp)


    def _check(self):
        if np.isinf(pd.Series(self.algo)).any():
            raise Exception('AlgoEvent algo exists inf value!')



#-----------------------------------------------------------------------------------------
class OrderEvent(Event):
    """
    发送订单到交易所
    """

    def __init__(self, order_name, order_dict, timestamp):
        """
        order_name - 可以填写portfolio name, 或者signal name
        order_dict: key - value e.g. {"000001":{"xxx":   xxx}}
                                                委托日期: “”
                                                委托时间: “”
                                                证券代码: “”
                                                证券名称: “”
                                                买卖方向: 卖
                                                委托状态: “未成交”
                                                委托价格: #小数点后三位
                                                委托数量: int
                                                市场类别: “深圳A股”
                                                订单类型: “正常委托”
                                                委托编号: “”

        """
        self.event_type = "ORDER"
        self.order_name = order_name
        self.order_dict = order_dict
        self.timestamp = timestamp
        self._check()


    def __str__(self):
        return "[OrderEvent] %s %s" %(self.order_name, self.timestamp)


    def _check(self):
        # print(pd.DataFrame(self.order_dict).loc['quantity'].values)
        # if (pd.DataFrame(self.order_dict).loc['quantity'].values <=0).any():
        #     raise Exception('OrderEvent exists zero or <0 quantity!')
        pass




#-----------------------------------------------------------------------------------------
class FillEvent(Event):
    """
    交易所返回，实际成交订单，包括标的，成交价，手续费等
    """

    def __init__(self, fill_dict, timestamp):
        """
        Initialises the FillEvent object.
        timestamp: 订单成交的时间戳
        fill_dict: key - value e.g. {"000001":{"xxx":    xxx}}
                                                成交日期: 
                                                成交时间: 
                                                证券代码: “”
                                                证券名称: “”
                                                买卖方向: 卖
                                                成交额:
                                                成交状态: “成交”
                                                成交价格: #小数点后三位
                                                成交数量: int
                                                成交价格: #小数点后三位
                                                市场类别: “深圳A股”
                                                订单类型: “正常成交”
                                                委托编号: “”
                                                佣金:     5.000
                                                印花税:   4.510
                                                过户费:   0.090
                                                结算费用: 0.000

        """
        self.event_type = "FILL"
        self.fill_dict = fill_dict
        self.timestamp = timestamp
        self._check()


    def __str__(self):
        return "[FillEvent] %s" %(self.timestamp)


    def _check(self):
        # if (pd.DataFrame(self.fill_dict)['quantity'].values < 0).any():
        #     raise Exception('FillEvent exists <0 quantity!')
        pass




