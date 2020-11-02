from multiprocessing import Pool
from .log import logger
log = logger('[load_files]')
import pandas as pd

def load_csv(csv_path):
    log.info('[read_csv] csv_path:%s' %csv_path)
    df = pd.read_csv(csv_path, index_col='TradingTime', dtype={'Symbol':str})
    return df


def multi_process_read_csv(csv_path_list, pool_num=10):
    csv_dict = {}
    pool = Pool(pool_num) 
    for csv_path in csv_path_list:
        pool.apply_async(load_csv, (csv_path,), callback=csv_dict.update)
    pool.close()
    pool.join()
    return csv_dict


def batch_read_csv(csv_path_list, method):
    csv_dict = {}
    for csv_path in csv_path_list:
        df = load_csv(csv_path)
        df = df.fillna(method=method)
        csv_dict.update({csv_path:df})
    return csv_dict
