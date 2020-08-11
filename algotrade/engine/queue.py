# %load_ext autoreload
# %autoreload 2
from queue import Queue, Empty
from threading import Thread
from ..utils.log import logger
log = logger('[SimQueue]')


class EventQueue(object):

    def __init__(self):
        """
        __queue - event object list
        __active - event activate button
        __thread - event process thread
        """
        self.__queue = Queue()
        self.__active = False
        self.__handlers = {}

    #----------------------------------------------------------------------
    def run(self):
        while True:
            try:
                event = self.__queue.get(block=False) #block=True, timeout=1)
                self.__process(event)
            except Empty:
                return



    #----------------------------------------------------------------------
    def __process(self, event):
        if event.event_type in self.__handlers:
            for handler in self.__handlers[event.event_type]:
                # 这里handler会调用自身的on_event方法，e.g. on_bar(), on_signal()...
                getattr(handler, 'on_'+event.event_type.lower())(event)


    #----------------------------------------------------------------------
    def register(self, event_type, handler):
        try:
            handlerList = self.__handlers[event_type]
        except KeyError:
            handlerList = []
         
        self.__handlers[event_type] = handlerList

        if handler not in handlerList:
            handlerList.append(handler)
        log.info('register handler for event: %s' %event_type)



    #----------------------------------------------------------------------
    def unregister(self, event_type, handler):
        try:
            handlerList = self.__handlers[event_type]
        except KeyError:
            handlerList = []

        if handler in handlerList:
            handlerList.remove(handler)

        if not handlerList:
            del self.__handlers[event_type]
        log.info('unregister handler: %s' %event_type)


    #----------------------------------------------------------------------
    def put(self, event):
        log.info(event)
        self.__queue.put(event)



