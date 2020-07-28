from __future__ import print_function

from abc import ABCMeta


class AbstractPriceHandler(object):

    __metaclass__ = ABCMeta






class AbstractTickHandler(AbstractPriceHandler):
    def _subscribe_ticker(self):
        pass


    def _subscribe_fields(self):
        pass

    def update_tick(self):
        pass






