from tools.timer import Time
import traceback
import sys
import os
from threading import Lock, get_ident, current_thread
from functools import wraps


# import inspect

# 获取被调用函数所在模块文件名
# print(inspect.stack()[1][1])
# print(sys._getframe(1).f_code.co_filename)

# 获取被调用函数名称
# print(inspect.stack()[1][3])
# print(sys._getframe(1).f_code.co_name)

# 获取被调用函数在被调用时所处代码行数
# print(inspect.stack()[1][2])
# print(sys._getframe(1).f_lineno)


class Logger(object):
    def __init__(self, level=0, full='None'):
        self.time = Time()
        self.time.set_fmt('%H:%M:%S')
        self.level = level
        self.full = full
        self.attri_list = None
        self.mode = None
        self.pre_module = None
        self.pre_func = None
        self.line_num = None
        self.fmt = None
        self.log_dict = None

    def info(self, msg):
        level = 1
        if level >= self.level:
            mode = self.mode[level - 1]
            print(self.fmt.format(mode, msg))

    def warning(self, msg):
        level = 2
        if level >= self.level:
            mode = self.mode[level - 1]
            print(self.fmt.format(mode, msg))

    def error(self, msg=None):
        level = 3
        if level >= self.level:
            mode = self.mode[level - 1]
            type_, value_, traceback_ = sys.exc_info()
            ex = traceback.format_exception(type_, value_, traceback_)
            print(self.fmt.format(mode, '\033[1;31m{}\033[0m'.format('*' * 100)))
            for i in ex[1:]:
                print(self.fmt.format(mode, i.splitlines(True)[0].strip()))

            if msg:
                print(self.fmt.format(mode, msg))
            print(self.fmt.format(mode, '\033[1;31m{}\033[0m'.format('*' * 100)))

    def log(self, level=0, attri_list=['time', 'thread', 'func'], full=False):
        def L(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.mode = ['\033[1;32mINFO\033[0m', '\033[1;33mWARNING\033[0m', '\033[1;31mERROR\033[0m']
                self.time = Time()
                self.time.set_fmt('%H:%M:%S')
                self.pre_module = sys._getframe(1).f_code.co_filename.split('/')[-1].split('.')[0]
                self.pre_func = func.__qualname__
                self.line_num = sys._getframe(1).f_lineno
                self.fmt = '\r'
                self.log_dict = None
                self.log_dict = {
                    'time': '[{}] '.format(self.time.get_fmt_time),
                    'thread': '[{}] '.format(current_thread().name),
                    'module': '[{}] '.format(self.pre_module),
                    'func': '[{}] '.format(self.pre_func),
                    'num': '[{}] '.format(self.line_num),
                    'index': '[{}|{} {}] '.format(self.pre_module, self.pre_func, self.line_num)
                }
                Full = full
                if self.full != 'None':
                    Full = self.full
                if Full:
                    self.attri_list = ['time', 'thread', 'index']
                else:
                    self.attri_list = attri_list
                for i in self.attri_list:
                    self.fmt = self.fmt + self.log_dict[i]
                self.fmt = self.fmt + '[{}]: {}'
                return func(*args, **kwargs)

            return wrapper

        return L


def __call__(self, *args, **kwargs):
    self.info(args, kwargs)
