import heapq


class PriorityQueue:
    def __init__(self):
        self._queue = []

    def push(self, item, priority):
        heapq.heappush(self._queue, (priority, item))

    def pop(self):
        return heapq.heappop(self._queue)[-1]

    def empty(self):
        return True if not self._queue else False

    def qsize(self):
        return len(self._queue)
