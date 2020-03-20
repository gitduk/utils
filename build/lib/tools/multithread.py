from threading import Thread
import time
import threading
from tools.logger import Logger
from concurrent.futures.thread import ThreadPoolExecutor
from tools.queue import Queue


class RUNThread(object):
    def __init__(self, thread):
        self.thread = thread
        self.run()

    def run(self):
        if isinstance(self.thread, list):
            for thread in self.thread:
                thread.start()
            for thread in self.thread:
                thread.join()
        elif isinstance(self.thread, (Thread, MYThread)):
            self.thread.start()
            self.thread.join()


class ThreadPool(object):
    def __init__(self, max_workers, info=False):
        self.max_workers = max_workers
        self._task_queue = Queue()
        self.waiting_list = []
        self.working_list = []
        self.logger = Logger()
        self.info = info
        self.stop = False

    @property
    def task_queue(self):
        return self._task_queue

    def add_task(self, func, *args, **kwargs):
        if isinstance(args[0], tuple):
            task = (func, args[0], kwargs)
        else:
            task = (func, args, kwargs)
        self.task_queue.put(task)

    def add_task_list(self, func, arg_list):
        for i in arg_list:
            self.add_task(func, i)

    def wait_work_done(self):
        for i in self.waiting_list:
            i.start()
            self.waiting_list.remove(i)
            self.working_list.append(i)
        for i in self.working_list:
            if not i.is_alive():
                i.join()
                if self.info:
                    self.logger.info(
                        '-' * 30 + ' Queue Length is {}, {} workers is working '.format(self.task_queue.length,
                                                                                        len(
                                                                                            self.working_list)) + '-' * 30)
                self.working_list.remove(i)

    def execute_task(self):
        if self.task_queue.length < self.max_workers:
            self.max_workers = self.task_queue.length
        if self.info:
            self.logger.info(
                '-' * 30 + ' Queue Length is {}, {} workers is working '.format(self.task_queue.length,
                                                                                self.max_workers) + '-' * 30)
        while not self.stop:
            time.sleep(1)
            while len(self.waiting_list) + len(
                    self.working_list) < self.max_workers and self.task_queue.length != 0:
                func, args, kwargs = self.task_queue.get()
                worker = Thread(target=func, args=args, kwargs=kwargs)
                self.waiting_list.append(worker)
                self.wait_work_done()
            if len(self.working_list) != 0:
                self.wait_work_done()
            else:
                self.stop = True

