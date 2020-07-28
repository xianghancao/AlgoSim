
## Update
V1.0.0
Feb 21, 2020 - 初步完成了所计划的功能：事件和事件处理模块，统计和绘图
V1.1.0
Feb 27, 2020 - 补充了基于unittest的测试模块，用来测试各个handler
v1.2.0
Mar 1, 2020 - 统计每个标的物平均每天买入和卖出的数量
			  纠正了pnl累计收益计算的错误
v1.3.0
Mar 13, 2020 - profiling.py 加入alpha计算
tearsheet.py加入alpha绘图
v1.4.0
Mar 24, 2020 - logbook加入文件存储






## 事件和对应的处理方法

| 事件           | Handler      |
| -------------- | ------------ |
| TickEvent      | price_handler |
| BarEvent       | signal_handler     |
| SignalEvent    | portfolio_handler    |
| OrderEvent | execution_handler     |
| FillEvent     | position_handler     |


## 缩写表

| 缩写 | 解释 |
| ---- | ---- |
|      |      |
|      |      |
|      |      |
|      |      |
|      |      |
|      |      |
|      |      |
|      |      |





## Problems
### 成交额包括手续费么
“成交额不包括手续费,成交金额即是成交数量乘于成交价格。手续费和印花税都是按成交金额来计算的。”

核对交易状态，不能交易的标的，被剔除，不会推送到队列中？

如果股票复盘后，k线该怎样处理？

一只股票停牌后，其他股票的权重该怎样划分？

交易时订单没有反馈，怎样处理？





