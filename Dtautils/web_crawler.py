import json
import logging
import time

import urllib3
from parsel import Selector
import requests
from requests import Request, Session
from requests.cookies import cookiejar_from_dict, create_cookie
from Dtautils.data_factory import Printer, DataGroup, DataIter
from Dtautils.tools import PriorityQueue
from queue import Queue

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class SpiderUpdater(object):
    UA = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }

    def __init__(self, url=None, body=None, header=None, cookie=None, overwrite=True):

        if not header: header = self.UA

        self.method = 'POST' if body else 'GET'
        self.post_type = None
        if body: self.post_type = 'form' if '=' in body else 'payload'

        self._spider = {
            'path': self._string_to_dict(url, tag='path'),
            'body': self._string_to_dict(body, tag='body'),
            'param': self._string_to_dict(url, tag='param'),
            'header': {**self.UA, **self._string_to_dict(header, tag='header')},
            'cookie': cookiejar_from_dict(self._string_to_dict(cookie, tag='cookie')),
        }

        self.overwrite = overwrite
        self.referer = None

    @property
    def url(self):
        return self.path + self.param if self.path else ''

    @url.setter
    def url(self, url):
        self._spider['path'] = self._string_to_dict(url, tag='path')
        self._spider['param'] = self._string_to_dict(url, tag='param')

        if self.headers.get('Host'): self.update('Host', self._spider['path'].get('domain'), tag='header')

    @property
    def path(self):
        path_dict = self._spider.get('path')
        assert path_dict, 'Please set a url for Spider'

        protocol = path_dict.get('protocol')
        domain = path_dict.get('domain')
        sub_path = '/'.join([value for key, value in path_dict.items() if key not in ['protocol', 'domain']])
        return f'{protocol}://{domain}/{sub_path}'

    @property
    def path_dict(self):
        return self._spider.get('path')

    @path.setter
    def path(self, path):
        self._spider['path'] = self._string_to_dict(path, tag='path')

    @property
    def param(self):
        if not self._spider.get('param'): return ''
        param_str = '&'.join([f'{key}={value}' for key, value in self._spider.get('param').items()])
        return '?' + param_str

    @property
    def param_dict(self):
        return self._spider.get('param')

    @param.setter
    def param(self, params):
        self._spider['param'] = self._string_to_dict(params, tag='param')

    @property
    def body(self):
        if not self.post_type: return ''

        body = self._spider.get('body')
        if self.post_type == 'form':
            return '&'.join([f'{key}={value}' for key, value in body.items()])
        else:
            return json.dumps(body)

    @property
    def body_dict(self):
        return self._spider.get('body')

    @body.setter
    def body(self, body):
        self._spider['body'] = self._string_to_dict(body, tag='body')

    @property
    def headers(self):
        if self.referer: self._spider['header']['referer'] = self.referer
        return self._spider.get('header')

    @headers.setter
    def headers(self, header):
        self._spider['header'] = self._string_to_dict(header, tag='header')

    @property
    def cookies(self):
        return self._spider.get('cookie').get_dict()

    @cookies.setter
    def cookies(self, cookie):
        assert isinstance(cookie, (dict, str)), f'cookie must be string or dict, get {cookie}'
        if isinstance(cookie, str):
            cookie = self._string_to_dict(cookie, tag='cookie')

        self._spider['cookie'] = cookiejar_from_dict(cookie)

    @property
    def cookie_jar(self):
        return self._spider.get('cookie')

    @property
    def _spider_keys(self):
        keys = {}
        for key in self._spider.keys():
            keys[key] = list(self._spider.get(key).keys())
        return keys

    @property
    def spider(self):
        return self._spider

    def update_cookie_from_header(self):
        cookie = self.headers.get('Cookie')
        if cookie:
            cookie_dict = self._string_to_dict(cookie, tag='cookie')
            self.update(cookie_dict, tag='cookie')
        else:
            print('There is no cookie in spider header')

    def update_cookie_from_resp(self, resp):
        if hasattr(resp, 'cookies'):
            self._spider['cookie'].update(resp.cookies)

    def update(self, *args, tag=None, prepare=False):
        assert False not in [isinstance(_, str) for _ in args], f'args must be str, get {args}'
        key, value = args
        self._update(key, value, tag=tag)
        if prepare:
            prepared_request = Request(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                       method=self.method).prepare()
            prepared_request.priority = 0
            return prepared_request

    def update_from_list(self, *args, tag=None, prepare=False):
        assert len(args) == 2 and False not in [isinstance(_, list) for _ in args], f'args must be list, get {args}'

        for key, value in zip(args):
            self._update(key, value, tag=tag)

        if prepare:
            prepared_request = Request(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                       method=self.method).prepare()
            prepared_request.priority = 0
            return prepared_request

    def update_from_dict(self, *args, tag=None, prepare=False):
        if len(args) == 1:
            assert isinstance(args[0], dict), f'args must be dict, get {args}'

            for key, value in args[0].items():
                self._update(key, value, tag=tag)

        elif len(args) == 2:
            assert False not in [isinstance(_, dict) for _ in args], f'args must be dict, get {args}'

            for key, value in args[0].items():
                value = args[1].get(value)
                self._update(key, value, tag=tag)
        else:
            raise Exception(f'Update Error ... unsupported update args {args}')

        if prepare:
            prepared_request = Request(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                       method=self.method).prepare()
            prepared_request.priority = 0
            return prepared_request

    def _update(self, key, value, tag=None):
        if not tag: tag = self._auto_set_tag(key)

        self.referer = self.url

        assert tag in ['path', 'param', 'body', 'header', 'cookie'], f'Update failed ... no tag {key}:{value}'

        if tag != 'cookie':
            self._spider[tag][key] = value
        else:
            if key in [_.name for _ in self._spider.get('cookie')] and self.overwrite:
                current_cookie = [_ for _ in self._spider.get('cookie') if _.name == key][0]
                new_cookie = create_cookie(key, value, domain=current_cookie.domain, path=current_cookie.path)
                self._spider[tag].set_cookie(new_cookie)
            else:
                self._spider[tag].set(key, value)

    def _auto_set_tag(self, key):
        tag_name_list = [tag_name for tag_name, key_list in self._spider_keys.items() if key in key_list]
        assert len(tag_name_list) <= 1, f'Please set tag for update, there are many tags: {tag_name_list}'

        tag_d = {
            'GET': 'param',
            'POST': 'body'
        }
        tag = tag_name_list[0] if tag_name_list else tag_d.get(self.method)

        return tag

    def _string_to_dict(self, string, tag=None):
        result = {}
        if not string: return result if tag != 'cookie' else requests.cookies.RequestsCookieJar()
        if isinstance(string, dict): return string

        string = string.strip()

        if tag == 'path' and '://' in string:
            if '?' in string: string = string.split('?')[0]

            protocol = string.split('://', 1)[0]
            domain = string.split('://', 1)[1].split('/')[0]
            path_list = string.split('://', 1)[1].split('/')[1:]

            result['protocol'] = protocol
            result['domain'] = domain
            result = {**result, **dict(zip(path_list, path_list))}

        if tag == 'param':
            if self.method == 'POST': return result

            if '?' in string:
                if '=' in string:
                    string = string.split('?')[-1]
                    result = dict(
                        [_.split('=', 1) for _ in string.split('&') if '=' in _ and not _.endswith('=')])
                    result = {**result, **dict([(_.strip('='), '') for _ in string.split('&')
                                                if _.endswith('=') or '=' not in _])}
                else:
                    result = dict([(string, string) for _ in string.split('&')])

            elif '=' in string:
                result = dict([_.split('=', 1) for _ in string.split('&')])
            else:
                result = {}

        if tag == 'body':
            if '=' in string and '&' in string:
                result = dict([_.split('=', 1) for _ in string.split('&')])
            elif '=' in string:
                result = dict([string.split('=')])
            elif ':' in string:
                result = json.loads(string)

        if tag == 'header' or tag == 'cookie':
            split_params = ['\n', ':'] if tag == 'header' else [';', '=']
            for field in string.split(split_params[0]):
                keys = result.keys()

                key, value = field.split(split_params[1], 1)
                key, value = [key.strip(), value.strip()]

                value_in_dict = result.get(key)
                if key in keys and isinstance(value_in_dict, str):
                    result[key] = [value_in_dict, value]
                elif isinstance(value_in_dict, list):
                    result[key].append(value)
                else:
                    result[key] = value

        return result

    def preview(self, data=None, name=None):
        if not data:
            name = 'Spider'
            data = {
                'url': self.url,
                'param': self.param,
                'body': self.body,
                'headers': self.headers,
                'cookies': self.cookies
            }
        else:
            name = name or type(data).__name__
            if not isinstance(data, dict): return data

        d_group = DataGroup(name)
        for key, value in data.items():
            if isinstance(value, str):
                d_group.add_info(key, value)
            else:
                d_group.add_data(key, value)

        printer = Printer()
        lines = printer.parse_data_group(d_group)
        return '\n'.join(lines)

    def __repr__(self):
        return self.preview()


class SpiderExtractor(object):
    def find(self, *rules, data=None, match_mode=None, re_method='search', group_index=None):
        result = DataIter(*rules, data=data, mode='search', match_mode=match_mode, re_method=re_method,
                          group_index=group_index)
        return result.result

    def extractor(self, *rules, data=None, extract=True, first=False, replace_rule=None, extract_key=False,
                  extract_method=None):

        assert extract_method in ['css', 'xpath'], f'Unsupported extract method: {extract_method}'
        tree = Selector(data)

        result = {}

        if len(rules) == 1 and isinstance(rules[0], str):
            result = self._get_result(tree, rules[0], method=extract_method)
            ...

        elif len(rules) == 1 and isinstance(rules[0], dict):
            for key, rule in rules[0].items():
                if extract_key:
                    key = self._get_result(tree, key, method=extract_method)
                    key = key.extract() if not first else key.extract_first()
                result[key] = self._get_result(tree, rule, method=extract_method)
        else:
            print(f'Rule Format Error ... unsupported rule format {rules}')

        if extract and isinstance(result, dict):
            for key, value in result.items():
                result[key] = self._extract_selector(value, first=first)
        elif extract:
            result = self._extract_selector(result, first=first)

        if replace_rule:
            diter = DataIter(replace_rule, data=result)
            result = diter.result

        return result

    @staticmethod
    def _extract_selector(value, first=None):
        if hasattr(value, 'extract'):
            return value.extract() if not first else value.extract_first()
        else:
            value = [_.extract() if not first else _.extract_first() for _ in value if _.extract()]
            return value[0] if len(value) == 1 else value

    @staticmethod
    def _get_result(tree, rule, method=None):
        if '|' not in rule:
            result = tree.css(rule) if method == 'css' else tree.xpath(rule)
        else:
            result = [tree.css(_) if method == 'css' else tree.xpath(rule) for _ in rule.split('|')]

        return result


class SpiderDownloader(object):
    def __init__(self, timeout=10, stream=False, verify=None, allow_redirects=True, proxies=None, wait=None, cert=None,
                 retry=0, not_retry_code=None):
        self.download_count = 0
        self.session = Session()
        self._prepare_request_queue = PriorityQueue()
        self._resp_queue = Queue()

        self.timeout = timeout
        self.stream = stream
        self.verify = verify
        self.allow_redirects = allow_redirects
        self.proxies = proxies
        self.cert = cert
        self.wait = wait
        self.retry = retry
        self.not_retry_code = not_retry_code or [200]

    @property
    def prepare_request(self):
        return self._prepare_request_queue.pop() if not self._prepare_request_queue.empty() else None

    @prepare_request.setter
    def prepare_request(self, req):
        self._prepare_request_queue.push(req, 0)

    @property
    def resp(self):
        if self._resp_queue.empty(): self.request()
        return self._resp_queue.get() if not self._resp_queue.empty() else None

    @resp.setter
    def resp(self, resp):
        self._resp_queue.put(resp)

    @property
    def resp_data(self):
        resp = self.resp
        data = resp.text
        if data:
            if '<html' not in data and '</html>' not in data: data = json.loads(data)
        else:
            print(f'response body is empty!\n{resp}')

        return data

    @property
    def count(self):
        return {'req': self._prepare_request_queue.qsize(), 'resp': self._resp_queue.qsize(),
                'download': self.download_count}

    def request(self, **kwargs):
        if self.wait: time.sleep(self.wait)
        prepared_request = self.prepare_request
        if prepared_request:
            kwargs = {'timeout': self.timeout,
                      'stream': self.stream,
                      'verify': self.verify,
                      'allow_redirects': self.allow_redirects,
                      'proxies': self.proxies,
                      'cert': self.cert, **kwargs}
            resp = self.session.send(prepared_request, **kwargs)
            self._resp_queue.put(resp)
            self.download_count += 1

            if self.retry > prepared_request.priority and resp.status_code not in self.not_retry_code:
                prepared_request.priority = prepared_request.priority + 1
                self._prepare_request_queue.push(prepared_request, prepared_request.priority)

            return resp
        else:
            print('No prepared request error ... spider prepare request queue is empty!')


class Spider(SpiderUpdater, SpiderDownloader, SpiderExtractor):
    def __init__(self, url=None, body=None, header=None, cookie=None, overwrite=True, timeout=10, stream=False,
                 verify=None, allow_redirects=True, proxies=None, wait=None, cert=None, retry=0, not_retry_code=None):

        super(Spider, self).__init__(url=url, body=body, header=header, cookie=cookie, overwrite=overwrite)

        SpiderDownloader.__init__(self, timeout=timeout, stream=stream, verify=verify, allow_redirects=allow_redirects,
                                  proxies=proxies, wait=wait, cert=cert, retry=retry, not_retry_code=not_retry_code)

        if url:
            prepare_request = Request(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                      method=self.method).prepare()
            prepare_request.priority = 0
            self._prepare_request_queue.push(prepare_request, prepare_request.priority)

    def update(self, *args, tag=None, prepare=False):
        prepared_request = SpiderUpdater.update(self, *args, tag=tag, prepare=prepare)
        if prepare: self._prepare_request_queue.push(prepared_request, 0)

    def update_from_list(self, *args, tag=None, prepare=False):
        prepared_request = SpiderUpdater.update_from_list(self, *args, tag=tag, prepare=prepare)
        if prepare: self._prepare_request_queue.push(prepared_request, 0)

    def update_from_dict(self, *args, tag=None, prepare=False):
        prepared_request = SpiderUpdater.update_from_dict(self, *args, tag=tag, prepare=prepare)
        if prepare: self._prepare_request_queue.push(prepared_request, 0)

    def find(self, *rules, data=None, match_mode=None, re_method='search', group_index=None):
        if not data: data = self.resp_data

        return SpiderExtractor.find(self, *rules, data=data, match_mode=match_mode, re_method=re_method,
                                    group_index=group_index)

    def css(self, *rules, data=None, extract=True, first=True, replace_rule=None, extract_key=False):
        if not data: data = self.resp_data
        result = SpiderExtractor.extractor(self, *rules, data=data, extract_method='css', extract=extract, first=first,
                                           replace_rule=replace_rule,
                                           extract_key=extract_key)
        return result

    def xpath(self, *rules, data=None, replace_rule=None, extract_key=False):
        if not data: data = self.resp_data
        result = SpiderExtractor.extractor(self, *rules, data=data, extract_method='xpath', replace_rule=replace_rule,
                                           extract_key=extract_key)
        return result
