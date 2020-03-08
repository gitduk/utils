from threading import Thread
from tools.logger import Logger


class MYThread(object):
    def __init__(self, func, *args, daemon=False, **kwargs):
        self.daemon = daemon
        self.thread = Thread(target=func, args=args, kwargs=kwargs)
        self.logger = Logger()

    def set_daemon(self):
        self.daemon = True

    def start(self):
        self.logger.info('Start {}'.format(self.thread.name))
        self.thread.setDaemon(self.daemon)
        self.thread.start()

    def join(self):
        self.thread.join()
        self.logger.info('Exit {}'.format(self.thread.name))


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
        elif isinstance(self.thread, Thread):
            self.thread.start()
            self.thread.join()
