import time
import threading
from tools.logger import Logger


class Queue(object):
    def __init__(self):
        self._queue = []
        self.logger = Logger()

    @property
    def queue(self):
        return self._queue

    def put(self, item):
        self.queue.append(item)

    def get(self):
        if not self.empty():
            return self.queue.pop(0)
        else:
            self.logger.warning('Queue is empty!')

    def empty(self):
        length = len(self.queue)
        if length == 0:
            return True
        else:
            return False

    @property
    def length(self):
        return len(self.queue)

    def __repr__(self):
        return '{}|{}'.format(self.length, self.queue)
