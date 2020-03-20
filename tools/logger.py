from tools.timer import Time
import traceback
import sys
import os
from threading import get_ident, current_thread, Lock
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
    def __init__(self, level=0, full=None):
        self.level = level
        self.mode = ['\033[1;32mINFO\033[0m', '\033[1;33mWARNING\033[0m', '\033[1;31mERROR\033[0m']
        self.time = Time()
        self.lock = Lock()
        self.time.set_fmt('%H:%M:%S')
        self.fmt = '\r[{}] [{}] [{}] [{}]: {}'
        # self.line_num = None
        self.pre_module = None
        self.pre_func = sys._getframe(1).f_code.co_name

    def sp(self, *msg):
        print('-' * 100)
        for i in msg:
            if isinstance(i, list):
                _num = len(i)
                print('Lenght:{}'.format(_num))
                num = _num // 10
                index = [i * 10 for i in range(0, num + 1)]
                for j in index:
                    print(i[j:j + 10])
            else:
                print(i)

    @property
    def prompt(self):
        # self.line_num = sys._getframe(1).f_lineno
        pre_module = sys._getframe(2).f_code.co_filename.split('/')[-1].split('.')[0]
        time = self.time.get_fmt_time
        thread_name = current_thread().name
        if thread_name == 'MainThread':
            self.pre_func = ''
        index = '{}{}'.format(pre_module, self.pre_func)
        return time, thread_name, index

    def info(self, msg, end='\n'):
        level = 1
        if level >= self.level:
            mode = self.mode[level - 1]
            prompt = self.prompt
            print(self.fmt.format(prompt[0], prompt[1], prompt[2], mode, msg), end=end)

    def warning(self, msg):
        level = 2
        if level >= self.level:
            mode = self.mode[level - 1]
            prompt = self.prompt
            print(self.fmt.format(prompt[0], prompt[1], prompt[2], mode, msg))

    def error(self, msg=None):
        level = 3
        if level >= self.level:
            mode = self.mode[level - 1]
            prompt = self.prompt
            type_, value_, traceback_ = sys.exc_info()
            ex = traceback.format_exception(type_, value_, traceback_)
            print(self.fmt.format(prompt[0], prompt[1], prompt[2], mode, '\033[1;31m{}\033[0m'.format('*' * 100)))
            for i in ex[1:]:
                print(self.fmt.format(prompt[0], prompt[1], prompt[2], mode, i.splitlines(True)[0].strip()))

            if msg:
                print(self.fmt.format(prompt[0], prompt[1], prompt[2], mode, msg))
            print(self.fmt.format(prompt[0], prompt[1], prompt[2], mode, '\033[1;31m{}\033[0m'.format('*' * 100)))

    def log(self, level=0):
        def L(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.pre_func = '|' + func.__qualname__
                return func(*args, **kwargs)

            return wrapper

        return L
