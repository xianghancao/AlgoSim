
import datetime, os
import pandas as pd

from ..utils.log import logger
log = logger('[TickHandler]')
from ..event import TimeEvent

class TimeIndex():
    def __init__(self, events_queue, date, store_path):
        self.events_queue = events_queue
        self.date = date
        self._init_timeindex()
        self._init_iterator()
        self.store_path = store_path
        self._iteration_end = False
        
    # ------------------------------------------------------------------------
    def _init_timeindex(self):
        """
        生成时间轴，3秒间隔的时间戳列表，负责全局迭代的索引
        """
        log.info('init timeindex...')

        delta = datetime.timedelta(days=0, seconds=3, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
        start = datetime.datetime(year=int(self.date[:4]), month=int(self.date[4:6]), day=int(self.date[6:8]), hour=9, minute=30, second=0, microsecond=0)
        self.timestamp_3s_list = []
        while True:
            self.timestamp_3s_list.append(start.strftime('%Y-%m-%d %H:%M:%S.000'))
            start = start+delta
            if start.hour >= 11 and start.minute >= 30: 
                break
            
        start = datetime.datetime(year=int(self.date[:4]), month=int(self.date[4:6]), day=int(self.date[6:8]), hour=13, minute=0, second=0, microsecond=0)
        while True:
            self.timestamp_3s_list.append(start.strftime('%Y-%m-%d %H:%M:%S.000'))
            start = start+delta
            if start.hour >= 14 and start.minute >= 55:
                break


    # ------------------------------------------------------------------------
    def _init_iterator(self):
        """
        迭代器，生成索引
        """
        self.timestamp_3s_iterator = (i for i in range(1, len(self.timestamp_3s_list)))


    # ------------------------------------------------------------------------
    def _update_iterator(self):
        try:
            self.iter_num = next(self.timestamp_3s_iterator)
        except StopIteration as e:
            log.info('The end of iteration')
            self._iteration_end = True
            return

    # ------------------------------------------------------------------------
    def _update_timestamp(self):
        self.timestamp = self.timestamp_3s_list[self.iter_num]
        self.previous_timestamp = self.timestamp_3s_list[self.iter_num-1]


    def _update_event(self):
        time_event = TimeEvent(timestamp=self.timestamp,
                                previous_timestamp=self.previous_timestamp)
        self.events_queue.put(time_event)
        return 
    
    def update_timeindex(self):
        self._update_iterator()
        if self._iteration_end: return
        self._update_timestamp()
        self._update_event()
    
    def get_all_timestamp(self):
        return self.timestamp_3s_list
    
    def store(self):
        df = pd.DataFrame(self.timestamp_3s_list, columns=['timeindex'])
        if not os.path.exists(self.store_path):
            os.mkdir(self.store_path)
        df.to_csv(os.path.join(self.store_path, 'timeindex.csv'))

