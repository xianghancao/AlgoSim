## 1. 更新

V1.0.0
Jul 20, 2020 -初步完成数据和算法的顺利运行



## 2. 概况

### 2.1 事件和模块

| 事件           | 模块  | 描述 |
| -------------: | -----------: | :------------- |
| TickEvent      | price_handler | 生成价格事件 |
| AlgoEvent | algo_handler   | 生成算法事件 |
| OrderEvent | order_handler | 生成订单事件 |
| FillEvent | execution_handler | 负责回测和实盘 |
|      | position_handler     | 更新持仓和账簿 |
|  | statistics | 统计基准，PNL等 |
|  | utils | 包括日志，解析价格，performance等功能 |
|  | queue | 负责队列 |



## 3. tick_handler

### 3.1 主要数据结构

timestamp_3s_list：3秒间隔的时间戳列表

tick_ticker_dict：键为股票代码，值为字段

tick_field_dict: 键为字段，值为股票代码

### 3.2 主要变量

timestamp_3s_iterator：对应timeindex的迭代器，负责全局迭代的索引iter_num

TAQ_iterator：对应TAQ数据的迭代器，负责TAQ数据迭代的索引TAQ_iter_num

TRADE_iterator：对应TRADE数据的迭代器，负责TRADE数据迭代的索引TRADE_iter_num

### 3.3 主要方法



##4. algo_handler 

### 4.1 主要数据结构



5.order_handler

6.execution_handler

7.position_handler

8.statistics

9 queue

## 10 常用示例





