import random

import requests
import threading
from queue import Queue
from Dtautils.settings import USER_AGENT_LIST


class Request(requests.sessions.Session, threading.Thread):
    __DEFAULT_THREAD_VALUE__ = [
        'name',
        'daemon'
    ]

    __DEFAULT_METHOD_VALUE__ = [
        'GET',
        'POST',
        'HEAD',
        'OPTIONS',
        'PUT',
        'PATCH',
        'DELETE'
    ]
    __DEFAULT_KEY__ = [
        'response_pool'  # 装响应的容器
        'priority'  # 请求优先级
        'use_session'  # 是否使用session
    ]

    def __init__(self, url, method='', *args, **kwargs):
        super().__init__()
        threading.Thread.__init__(self, name=kwargs.get('name'), daemon=kwargs.get('daemon'))

        self.url = url
        self.method = method.upper() or 'GET'
        assert self.method in self.__DEFAULT_METHOD_VALUE__, f'Invalid method {method}'
        self.request_kwargs = {key: value for key, value in kwargs.items() if key in self.__attrs__}

        self.response_pool = kwargs.get('response_pool') or Queue()
        self.priority = kwargs.get('priority')

    def run(self):
        assert hasattr(self.response_pool, 'put')
        self.request_kwargs.setdefault('headers', {'User-Agent': random.choice(USER_AGENT_LIST)})
        response = self.request(method=self.method, url=self.url, **self.request_kwargs)
        self.response_pool.put(response)

    @property
    def response(self):
        return self.response_pool.get_nowait()
