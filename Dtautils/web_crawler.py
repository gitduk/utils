import logging
import random
import urllib3
import requests
from requests import Session
from requests.cookies import cookiejar_from_dict, create_cookie, merge_cookies
from Dtautils.tools import *
from Dtautils.data_factory import update
from collections.abc import Iterable
from Dtautils.settings import USER_AGENT_LIST
from Dtautils.network.request import RequestThread

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class SpiderUpdater(object):
    __DEFAULT_REQUEST_VALUE__ = [
        'headers', 'cookies', 'auth', 'proxies', 'hooks', 'params', 'verify',
        'cert', 'adapters', 'stream', 'trust_env',
        'max_redirects', 'data', 'json'
    ]

    def __init__(
            self,
            url=None,
            method=None,
            data=None,
            json=None,
            headers=None,
            cookies=None,
            overwrite=True,
            max_retry=0,
            **kwargs
    ):
        self.method = method
        if not self.method: self.method = 'POST' if data or json else 'GET'

        self.spider = {
            'url': url_to_dict(url),
            'data': body_to_dict(data),
            'json': json_to_dict(json),
            'headers': {**self._init_header(), **headers_to_dict(headers)},
            'cookies': cookiejar_from_dict(cookies_to_dict(cookies)),
        }

        self.overwrite = overwrite
        self.referer = None

    def _init_header(self):
        if self.method == 'POST':
            content_type = 'application/x-www-form-urlencoded; charset=UTF-8'
            if self.spider.get('json'): content_type = 'application/json; charset=UTF-8'
            return {'User-Agent': random.choice(USER_AGENT_LIST), 'Content-Type': content_type}
        else:
            return {'User-Agent': random.choice(USER_AGENT_LIST)}

    @property
    def url(self):
        protocol = self.spider['url'].get('protocol')
        domain = self.spider['url'].get('domain')
        path = '/'.join(self.spider['url'].get('path'))
        _param = self.spider['url'].get('param')

        if len(_param) == 1 and len(set(list(_param.items())[0])) == 1:
            param = list(_param.values())[0]
        else:
            param = dict_to_body(_param)

        return f'{protocol}://{domain}/{path}?{param}'

    @url.setter
    def url(self, url):
        self.spider['url'] = url_to_dict(url)

    @property
    def body(self):
        body = self.spider.get('body')
        return dict_to_body(body)

    @property
    def body_dict(self):
        return self.spider.get('body')

    @body.setter
    def body(self, body):
        self.spider['body'] = body_to_dict(body)

    @property
    def json(self):
        return dict_to_json(self.spider.get('json'))

    @property
    def json_dict(self):
        return self.spider.get('json')

    @json.setter
    def json(self, json):
        self.spider['json'] = json_to_dict(json)

    @property
    def headers(self):
        return self.spider.get('headers')

    @headers.setter
    def headers(self, headers):
        self.spider['headers'] = headers_to_dict(headers)

    @property
    def cookies(self):
        return self.spider.get('cookie').get_dict()

    @cookies.setter
    def cookies(self, cookie):
        if isinstance(cookie, str): cookie = cookies_to_dict(cookie)

        self.spider['cookies'] = merge_cookies(self.spider.get('cookies'), cookie)

    @property
    def cookie_jar(self):
        return self.spider.get('cookies')

    def update_cookie_from_header(self):
        cookie = self.headers.get('Cookie')
        if cookie:
            cookie_dict = cookies_to_dict(cookie)
            self.spider['cookies'] = merge_cookies(self.spider.get('cookies'), cookie_dict)

    def update_cookie_from_resp(self, response):
        if hasattr(response, 'cookies'):
            self.spider['cookies'] = merge_cookies(self.spider.get('cookies'), response.cookies)

    def create_request_task(self, **kwargs):
        request_task = RequestThread(url=self.url, method=self.method, data=self.body, json=self.json_dict,
                                     headers=self.headers, cookies=self.cookies, **kwargs)
        return request_task

    def __repr__(self):
        return f'{type(self).__name__}({self.method}, url=\'{self.url}\', body=\'{self.body}\', headers={self.headers}, cookies={self.cookies})'


class SpiderDownloader(object):
    def __init__(
            self,
            timeout=10,
            stream=False,
            verify=None,
            allow_redirects=True,
            proxies=None,
            wait=0,
            cert=None,
            max_retry=0,
            not_retry_code=None):

        self.download_count = 0
        self.session = Session()
        self.prepared_request_queue = PriorityQueue()
        self.failed_list = []

        self.timeout = timeout
        self.stream = stream
        self.verify = verify
        self.allow_redirects = allow_redirects
        self.proxies = proxies
        self.cert = cert
        self.wait = wait
        self.pre_request = None

        self.max_retry = max_retry
        self.retry_code = not_retry_code or [404, 503]
        self.retry_count = 0
        self.start_time = time.time()
        self.running_time = None

    def pop_request(self):
        return self.prepared_request_queue.pop() if not self.prepared_request_queue.empty() else None

    def push_request(self, req, priority=0):
        self.prepared_request_queue.push(req, priority)

    @property
    def count(self):
        return {'Request': self.prepared_request_queue.qsize(), 'Downloaded': self.download_count,
                'Retried': self.retry_count, 'Failed': len(self.failed_list)}

    @property
    def speed(self):
        return round(self.download_count / self.running_time, 3)

    @staticmethod
    def _proxies_filter(proxies):
        assert isinstance(proxies, dict), 'Proxies must be a dict object!!!'
        if 'time' not in proxies.keys():
            return True
        else:
            return int(proxies.get('time')) > time.time()

    def get_proxies(self):
        if isinstance(self.proxies, dict):
            return self.proxies
        elif isinstance(self.proxies, Iterable):
            p_list = [_ for _ in self.proxies if self._proxies_filter(_)]
            if p_list:
                return random.choice(p_list)
            else:
                print('There are no valid agents.')

    def send_request(self):
        prepared_request = self.pop_request()
        if prepared_request is None: prepared_request = self.pre_request

        if prepared_request:
            time.sleep(self.wait or prepared_request.priority * 0.1)

            prepared_request.start()
            resp = prepared_request.response

            self.pre_request = prepared_request

            if resp.status_code in self.retry_code:
                if self.max_retry and prepared_request.priority <= self.max_retry:
                    prepared_request.priority = prepared_request.priority + 1
                    if prepared_request.priority - 1 == self.max_retry:
                        self.failed_list.append((prepared_request, resp))
                    else:
                        self.prepared_request_queue.push(prepared_request, prepared_request.priority)
                        self.retry_count += 1
                else:
                    self.failed_list.append((prepared_request, resp))
            else:
                self.download_count += 1
                self.running_time = round(time.time() - self.start_time, 3)

            return resp
        else:
            print('No prepared request ... spider prepare request queue is empty!')


class Spider(SpiderUpdater, SpiderDownloader):
    def __init__(
            self,
            url=None,
            body=None,
            headers=None,
            cookies=None,
            overwrite=True,
            post_type=None,
            timeout=10,
            stream=False,
            verify=None,
            allow_redirects=True,
            proxies=None,
            wait=None,
            cert=None,
            max_retry=0,
            not_retry_code=None,
    ):

        if url and url.endswith('/'): url = url[:-1]
        super(Spider, self).__init__(
            url=url,
            body=body,
            headers=headers,
            cookies=cookies,
            overwrite=overwrite,
            post_type=post_type
        )

        SpiderDownloader.__init__(
            self, timeout=timeout,
            stream=stream,
            verify=verify,
            allow_redirects=allow_redirects,
            proxies=proxies,
            wait=wait,
            cert=cert,
            max_retry=max_retry,
            not_retry_code=not_retry_code
        )
        if url:
            prepare_request = RequestThread(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                            method=self.method)
            prepare_request.priority = 0
            self.prepared_request_queue.push(prepare_request, prepare_request.priority)

    def update(self, *args, tag=None, prepare=True):
        prepared_request = SpiderUpdater.update(self, *args, tag=tag, prepare=prepare)
        if prepared_request: self.prepared_request_queue.push(prepared_request, 0)

    def update_from_dict(self, *args, tag=None, prepare=True):
        prepared_request = SpiderUpdater.update_from_dict(self, *args, tag=tag, prepare=prepare)
        if prepared_request: self.prepared_request_queue.push(prepared_request, 0)

    @property
    def url(self):
        return self.path + self.param if self.path else ''

    @url.setter
    def url(self, url):
        self.spider['path'] = self._string_to_dict(url, tag='path')
        self.spider['param'] = self._string_to_dict(url, tag='param')

        if self.headers.get('Host'): self.update('Host', self.spider['path'].get('domain'), tag='header')
        if self.prepare: self.prepared_request_queue.push(self.create_request_task(), 0)

    @property
    def body_form(self):
        if not self.post_type: return ''
        body = self.spider.get('body')
        return '&'.join(f'{key}={value}' for key, value in body.items())

    @body_form.setter
    def body_form(self, body):
        self.post_type = 'form'
        self.spider['body'] = self._string_to_dict(body, tag='body')
        if self.prepare: self.prepared_request_queue.push(self.create_request_task(), 0)

    @property
    def body_json(self):
        if not self.post_type: return ''
        body = self.spider.get('body')
        return json.dumps(body)

    @body_json.setter
    def body_json(self, body):
        self.post_type = 'payload'
        self.spider['body'] = self._string_to_dict(body, tag='body')
        if self.prepare: self.prepared_request_queue.push(self.create_request_task(), 0)

    def get(self, url=None, headers=None, **kwargs):
        resp = self.session.get(url or self.url, headers=headers or self.headers, **kwargs)
        self.cookies = self.session.cookies
        return resp

    def post(self, url=None, body=None, json=None, headers=None, **kwargs):
        if self.post_type == 'form':
            body = body or self.body_form
        else:
            json = json or self.body_dict
        resp = self.session.post(url or self.url, data=body, json=json, headers=headers or self.headers, **kwargs)
        self.cookies = self.session.cookies
        return resp

    def send_request(self):
        resp = SpiderDownloader.send_request(self)
        self.cookies = self.session.cookies
        return resp
