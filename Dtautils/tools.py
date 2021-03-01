import heapq
import time
from collections import defaultdict
from functools import wraps


class PriorityQueue:
    def __init__(self):
        self._queue = []
        self.index = 0

    def push(self, item, priority):
        heapq.heappush(self._queue, (priority, self.index, item))
        self.index += 1

    def pop(self):
        return heapq.heappop(self._queue)[-1]

    def empty(self):
        return True if not self._queue else False

    def qsize(self):
        return len(self._queue)


def fn_timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print("Function [{}] Spend {:.3f} s".format(func.__name__, end - start))
        return result

    return wrapper


def _flatten(item, ign=(str, bytes)):
    for k, v in item.items():
        if isinstance(v, dict) and not isinstance(v, ign):
            yield from _flatten(v)
        yield k, v


