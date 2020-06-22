import time


class Time(object):
    def __init__(self):
        self.fmt = "%Y-%m-%d %H:%M:%S"
        self.time = time.time()

    def set_fmt(self, fmt):
        self.fmt = fmt

    def sleep(self,n):
        time.sleep(n)

    @property
    def get_fmt_time(self):
        now = int(time.time())
        time_array = time.localtime(now)
        other_style_time = time.strftime(self.fmt, time_array)
        return other_style_time
