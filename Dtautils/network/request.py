import random
from requests.sessions import Session
import requests
import threading
from Dtautils.settings import USER_AGENT_LIST
from Dtautils.network.download import Response


class RequestThread(threading.Thread):
    __DEFAULT_THREAD_VALUE__ = [
        'name',
        'daemon'
    ]
    __DEFAULT_REQUEST_VALUE__ = [
        'headers', 'cookies', 'auth', 'proxies', 'hooks', 'params', 'verify',
        'cert', 'adapters', 'stream', 'trust_env',
        'max_redirects', 'data', 'json'
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
        'resp'  # 响应
        'priority'  # 请求优先级
        'use_session'  # 是否使用session
        'max_retry'  # 重试次数
    ]

    def __init__(self, url, method='', *args, **kwargs):
        super().__init__()
        threading.Thread.__init__(self, name=kwargs.get('name'), daemon=kwargs.get('daemon'))

        # 必要参数
        self.url = url
        self.method = method.upper() or 'GET'
        assert self.method in self.__DEFAULT_METHOD_VALUE__, f'Invalid method {method}'

        # 请求参数
        self.request_kwargs = {key: value for key, value in kwargs.items() if key in self.__DEFAULT_REQUEST_VALUE__}
        self.request_kwargs.setdefault('headers', {'User-Agent': random.choice(USER_AGENT_LIST)})
        if self.request_kwargs.get('data') or self.request_kwargs.get('json'): self.method = 'POST'

        # 自定义参数
        self.response = None
        self.priority = kwargs.get('priority') or 0
        self.max_retry = kwargs.get('max_retry') or 0
        self._retry_num = 0
        self.use_session = kwargs.get('use_session')
        self.session = Session() if self.use_session else None

    def run(self):
        if self.use_session:
            response = self.session.request(method=self.method, url=self.url, **self.request_kwargs)
        else:
            response = requests.request(method=self.method, url=self.url, **self.request_kwargs)

        if response.status_code != 200 and self.max_retry > 0:
            self.max_retry -= 1
            self.run()
            self._retry_num += 1
            msg = f'Retry-{self._retry_num}: [{self.method.upper()}] {response.url} {response.request.body or ""} {response.status_code}'
            print(msg)
        else:
            self.response = Response(response)


#
url = 'https://temp.163.com/special/00804KVA/cm_yaowen20200213_0{}.js?callback=data_callback&date=20200115'

pool = []
for i in range(2, 12):
    thread = RequestThread(url.format(i), max_retry=3, use_session=True)
    pool.append(thread)

for i in pool:
    i.start()

for i in pool:
    i.join()

for i in pool:
    if i.response.is_html:
        print(i.response)
    else:
        print(i.response.re('data_callback\((.*?)\)'))
