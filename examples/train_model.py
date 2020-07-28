import pandas as pd
import sys, os
import pdb
import warnings
warnings.filterwarnings('ignore')
sys.path.append('/home/cxh/Works/TradeWorks/AlgoTrade/')
from algotrade.algo_handler import model

def fn(date):
	

	print(date)
	path = '/mnt/ssd/AlgoTrade/data/%s/price' %date

	ActiveBuy = pd.read_csv(os.path.join(path, 'ActiveBuy.csv'), index_col=0)
	ActiveSell = pd.read_csv(os.path.join(path, 'ActiveSell.csv'), index_col=0)

	BuyVolume01 = pd.read_csv(os.path.join(path, 'BuyVolume01.csv'), index_col=0)[ActiveBuy.columns.values]
	SellVolume01 = pd.read_csv(os.path.join(path, 'SellVolume01.csv'), index_col=0)[ActiveBuy.columns.values]
	BuyPrice01 = pd.read_csv(os.path.join(path, 'BuyPrice01.csv'), index_col=0)[ActiveBuy.columns.values]
	SellPrice01 = pd.read_csv(os.path.join(path, 'SellPrice01.csv'), index_col=0)[ActiveBuy.columns.values]
	TotalBuyOrderVolume = pd.read_csv(os.path.join(path, 'TotalBuyOrderVolume.csv'), index_col=0)[ActiveBuy.columns.values]
	TotalSellOrderVolume = pd.read_csv(os.path.join(path, 'TotalSellOrderVolume.csv'), index_col=0)[ActiveBuy.columns.values]
	WtAvgSellPrice = pd.read_csv(os.path.join(path, 'WtAvgSellPrice.csv'), index_col=0)[ActiveBuy.columns.values]
	WtAvgBuyPrice = pd.read_csv(os.path.join(path, 'WtAvgBuyPrice.csv'), index_col=0)[ActiveBuy.columns.values]



	#pdb.set_trace()
	m = model.Model(dump_dir='/home/cxh/Works/TradeWorks/AlgoTrade/data/%s/reg_model.joblib' %date)
	m.cal_X(BuyVolume01.values, SellVolume01.values, BuyPrice01.values, SellPrice01.values,
	                TotalBuyOrderVolume.values, TotalSellOrderVolume.values, ActiveBuy.values, ActiveSell.values,
	                WtAvgSellPrice.values, WtAvgBuyPrice.values)
	m.cal_y(BuyPrice01.values, SellPrice01.values)
	m.fit()
	print(m.summary())
	#m.dump()


date = '20200608'
fn(date)
#for date in os.listdir('/mnt/ssd/AlgoTrade/data/'):
#	fn(date)
