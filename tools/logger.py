from tools.timer import Time


class Logger(object):
    def __init__(self, level=0):
        self.level = level
        self.fmt = '[{}] [{}]: {}'
        self.mode = ['INFO', 'WARNING']

    def info(self, msg):
        level = 1
        if level >= self.level:
            mode = self.mode[level - 1]
            time = Time()
            print(self.fmt.format(time.get_fmt_time(), mode, msg))

    def warning(self, msg):
        level = 2
        if level >= self.level:
            mode = self.mode[level - 1]
            print(self.fmt.format(Time.get_fmt_time, mode, msg))

