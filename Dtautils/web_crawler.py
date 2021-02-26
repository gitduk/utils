import json
import logging
import time
import sqlite3
import pymysql
import urllib3
from parsel import Selector as slctor
import requests
from requests import Request, Session
from requests.cookies import cookiejar_from_dict, create_cookie
from Dtautils.tools import PriorityQueue
from queue import Queue
from Dtautils.data_factory import replace, search, re_search, re_findall

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class SpiderUpdater(object):
    UA = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }

    def __init__(self, url=None, body=None, header=None, cookie=None, overwrite=True, prepare=True):

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
        self.prepare = prepare

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
            return '&'.join(f'{key}={value}' for key, value in body.items())
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

    def update(self, *args, tag=None, prepare=None):
        assert False not in (isinstance(_, str) for _ in args), f'args must be str, get {args}'

        key, value = args
        self._update(key, value, tag=tag)

        return self._get_prepared_request(prepare)

    def update_from_list(self, *args, tag=None, prepare=None):
        assert len(args) == 2 and False not in (isinstance(_, list) for _ in args), f'args must be list, get {args}'

        for key, value in zip(args):
            self._update(key, value, tag=tag)

        return self._get_prepared_request(prepare)

    def update_from_dict(self, *args, tag=None, prepare=None):
        if len(args) == 1:
            assert isinstance(args[0], dict), f'args must be dict, get {args}'

            for key, value in args[0].items():
                self._update(key, value, tag=tag)

        elif len(args) == 2:
            assert False not in (isinstance(_, dict) for _ in args), f'args must be dict, get {args}'

            for key, value in args[0].items():
                value = args[1].get(value)
                self._update(key, value, tag=tag)
        else:
            raise Exception(f'Update Error ... unsupported update args {args}')

        return self._get_prepared_request(prepare)

    def _get_prepared_request(self, prepare):
        if prepare is None:
            if self.prepare: return self._preparing_request()
        else:
            if prepare: return self._preparing_request()

    def _preparing_request(self):
        prepared_request = Request(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                   method=self.method).prepare()
        prepared_request.priority = 0

        return prepared_request

    def _update(self, key, value, tag=None):
        if not tag: tag = self._auto_set_tag(key)

        self.referer = self.url

        assert tag in ('path', 'param', 'body', 'header', 'cookie'), f'Update failed ... no tag {key}:{value}'

        if tag != 'cookie':
            self._spider[tag][key] = value
        else:
            if key in (_.name for _ in self._spider.get('cookie')) and self.overwrite:
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
            result = {**result, **{_: _ for _ in path_list}}

        if tag == 'param':
            if self.method == 'POST': return result

            if '?' in string:
                if '=' in string:
                    string = string.split('?')[-1]
                    result = {_.split('=', 1)[0]: _.split('=', 1)[1] for _ in string.split('&') if '=' in _}
                else:
                    result = {string.split('?')[-1]: '' for _ in string.split('&')}

            else:
                result = {}

        if tag == 'body':
            if '=' in string:
                result = {_.split('=', 1)[0]: _.split('=', 1)[1] for _ in string.split('&')}
            elif ':' in string:
                if '\'' in string: string = string.replace('\'', '"')
                result = json.loads(string)

        if tag == 'header' or tag == 'cookie':
            split_params = ['\n', ':'] if tag == 'header' else [';', '=']
            for field in string.split(split_params[0]):
                key, value = field.split(split_params[1], 1)
                result[key.strip()] = value.strip()

        return result

    def __repr__(self):
        return f'{type(self).__name__}({self.method}, url=\'{self.url}\', body=\'{self.body}\', headers={self.headers}, cookies={self.cookies})'


class SpiderExtractor(object):
    def find(self, key, data=None, target_type=None):
        return search(key=key, data=data, target_type=target_type)

    def extractor(self, *rules, data=None, extract=True, first=False, replace_map=None, extract_key=False,
                  extract_method=None):

        assert extract_method in ('css', 'xpath'), f'Unsupported extract method: {extract_method}'
        tree = slctor(data)

        result = {}

        if len(rules) == 1 and isinstance(rules[0], str):
            result = self._get_result(tree, rules[0], method=extract_method)

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

        if replace_map:
            result = replace(replace_map=replace_map, data=result)

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


class SpiderSaver(object):
    def __init__(self, path=None, host=None, port=None, user=None, password=None, database=None, charset=None,
                 **kwargs):
        assert path or host, 'Init Error ... path and host are None'
        self._save_path = path or ''
        self._file = None
        self.connect = None
        self.cursor = None

        self._host = host
        self._user = user
        self._password = password
        self._database = database
        self._port = port
        self._charset = charset or 'utf8mb4'

        self.mode = kwargs.get('mode') or 'a+'
        self._save_method = None
        self.csv_title = None

        self.insert_failed_list = []

        if path.split('.')[-1] == 'csv':
            self._init_file(**kwargs)
        else:
            self.table_name = kwargs.pop('insert_into')
            self._init_connect(**kwargs)

    @property
    def save_path(self):
        return self._save_path

    @save_path.setter
    def save_path(self, path, **kwargs):
        self._save_path = path
        if self._save_method == 'csv':
            self._init_file(**kwargs)
        else:
            self._init_connect(**kwargs)

    @property
    def file(self):
        return self._file

    @property
    def host(self):
        return self._host

    @property
    def user(self):
        return self._user

    @property
    def password(self):
        return self._password

    @property
    def database(self):
        return self._database

    @property
    def port(self):
        return self._port

    @property
    def charset(self):
        return self._charset

    def _init_file(self, **kwargs):
        self._file = open(self._save_path, self.mode, **kwargs) if self._save_path else None
        self._save_method = 'csv'

    def _init_connect(self, **kwargs):
        if not self._host:
            assert self._save_path.split('.')[-1] == 'db', f'Path Error ... {self._save_path}, path must end with .db'
            self.connect = sqlite3.connect(self._save_path, check_same_thread=False, **kwargs)
            self._save_method = 'sqlite'
        else:
            self.connect = pymysql.connect(host=self._host, port=self._port, user=self._user, password=self._password,
                                           database=self._database, charset=self._charset, **kwargs)
            self._save_method = 'mysql'

        self.cursor = self.connect.cursor() if self.connect else None

    def write(self, data):
        if self._save_method == 'csv': self._write_to_csv(data)
        if self._save_method == 'sqlite': self._write_to_sqlite(data)
        if self._save_method == 'mysql': self._write_to_mysql(data)

    def _write_to_csv(self, data):
        if not self.csv_title:
            if isinstance(data, dict): self.csv_title = list(data.keys())
            if isinstance(data, list): self.csv_title = list(range(len(data)))
            if self.csv_title: self._file.write(','.join(self.csv_title) + '\n')

        if isinstance(data, dict): self._file.write(','.join([str(_) for _ in data.values()]) + '\n')
        if isinstance(data, list): self._file.write(','.join([str(_) for _ in data]) + '\n')
        if isinstance(data, str): self._file.write(data + '\n')

    def _write_to_sqlite(self, data):
        assert self.table_name, 'Write To Sqlite Error ... missing table name'

        if isinstance(data, dict):
            values = '(' + ','.join(['? '] * len(data.values())) + ')'
            data = [str(_) for _ in data.values()]
        else:
            values = '(' + ','.join(['? '] * len(data)) + ')'

        try:
            self.cursor.execute(f'INSERT INTO {self.table_name} VALUES {values}', data)
        except sqlite3.IntegrityError:
            self.insert_failed_list.append(data)
        else:
            self.connect.commit()

    def _write_to_mysql(self, data):
        assert self.table_name, 'Write To Sqlite Error ... missing table name'

        if isinstance(data, dict):
            keys = (str(key) for key in data.keys())
            values = (str(value) for value in data.values())
            field_str = str(keys).replace("'", "")

            sql = f"insert into `{self.table_name}` {field_str} values {values};"
            try:
                self.cursor.execute(sql)
            except:
                self.insert_failed_list.append(data)
            else:
                self.connect.commit()
        else:
            raise Exception(f'Data Type Error ... data must be dict, get {type(data)}')

    def create_table(self, string):
        self.cursor.execute(string)
        self.connect.commit()


class SpiderDownloader(object):
    def __init__(self, timeout=10, stream=False, verify=None, allow_redirects=True, proxies=None, wait=0, cert=None,
                 max_retry=0, not_retry_code=None):
        self.download_count = 0
        self.session = Session()
        self.prepared_request_queue = PriorityQueue()
        self.resp_queue = Queue()
        self.failed_requests = []
        self.failed_resp = []

        self.timeout = timeout
        self.stream = stream
        self.verify = verify
        self.allow_redirects = allow_redirects
        self.proxies = proxies
        self.cert = cert
        self.wait = wait

        self.max_retry = max_retry
        self.retry_code = not_retry_code or [404]
        self.retry_count = 0
        self.start_time = time.time()
        self.running_time = None

    @property
    def prepared_request(self):
        return self.prepared_request_queue.pop() if not self.prepared_request_queue.empty() else None

    @prepared_request.setter
    def prepared_request(self, req):
        self.prepared_request_queue.push(req, 0)

    @property
    def resp(self):
        if self.resp_queue.empty(): self.request()
        return self.resp_queue.get() if not self.resp_queue.empty() else None

    @resp.setter
    def resp(self, resp):
        self.resp_queue.put(resp)

    @property
    def resp_data(self):
        resp = self.resp
        if resp and resp.text:
            if '<html' not in resp.text and '</html>' not in resp.text: return json.loads(resp.text)

        return resp.text if resp else ''

    @property
    def count(self):
        return {'request': self.prepared_request_queue.qsize(), 'response': self.resp_queue.qsize(),
                'downloaded': self.download_count, 'retried': self.retry_count, 'failed': len(self.failed_requests)}

    @property
    def speed(self):
        return round(self.download_count / self.running_time, 3)

    def request(self, **kwargs):
        prepared_request = self.prepared_request

        time.sleep(self.wait or prepared_request.priority * 0.1)
        if prepared_request:
            kwargs = {'timeout': self.timeout,
                      'stream': self.stream,
                      'verify': self.verify,
                      'allow_redirects': self.allow_redirects,
                      'proxies': self.proxies,
                      'cert': self.cert, **kwargs}
            resp = self.session.send(prepared_request, **kwargs)
            if resp.status_code in self.retry_code:
                if self.max_retry and prepared_request.priority <= self.max_retry:
                    prepared_request.priority = prepared_request.priority + 1
                    if prepared_request.priority - 1 == self.max_retry:
                        self.failed_requests.append(prepared_request)
                    else:
                        self.prepared_request_queue.push(prepared_request, prepared_request.priority)
                        self.retry_count += 1
                else:
                    self.failed_requests.append(prepared_request)
                    self.failed_resp.append(resp)
            else:
                self.resp_queue.put(resp)
                self.download_count += 1
                self.running_time = round(time.time() - self.start_time, 3)

            return resp
        else:
            print('No prepared request warning ... spider prepare request queue is empty!')


class Spider(SpiderUpdater, SpiderDownloader, SpiderExtractor, SpiderSaver):
    def __init__(self, url=None, body=None, header=None, cookie=None, overwrite=True, timeout=10, stream=False,
                 verify=None, allow_redirects=True, proxies=None, wait=None, cert=None, max_retry=0,
                 not_retry_code=None, prepare=True):

        super(Spider, self).__init__(url=url, body=body, header=header, cookie=cookie, overwrite=overwrite,
                                     prepare=prepare)

        if url:
            SpiderDownloader.__init__(self, timeout=timeout, stream=stream, verify=verify,
                                      allow_redirects=allow_redirects, proxies=proxies, wait=wait, cert=cert,
                                      max_retry=max_retry, not_retry_code=not_retry_code)

            prepare_request = Request(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                      method=self.method).prepare()
            prepare_request.priority = 0
            self.prepared_request_queue.push(prepare_request, prepare_request.priority)

    def update(self, *args, tag=None, prepare=None):
        prepared_request = SpiderUpdater.update(self, *args, tag=tag, prepare=prepare)
        if prepared_request: self.prepared_request_queue.push(prepared_request, 0)

    def update_from_list(self, *args, tag=None, prepare=None):
        prepared_request = SpiderUpdater.update_from_list(self, *args, tag=tag, prepare=prepare)
        if prepared_request: self.prepared_request_queue.push(prepared_request, 0)

    def update_from_dict(self, *args, tag=None, prepare=None):
        prepared_request = SpiderUpdater.update_from_dict(self, *args, tag=tag, prepare=prepare)
        if prepared_request: self.prepared_request_queue.push(prepared_request, 0)

    def find(self, key, data=None, target_type=None):
        return SpiderExtractor.find(self, key, data=data or self.resp_data, target_type=None)

    def re_search(self, re_map, data=None, index=None):
        return re_search(re_map=re_map, data=data or self.resp_data, index=index)

    def re_findall(self, re_map, data=None, index=None):
        return re_findall(re_map=re_map, data=data or self.resp_data)

    def css(self, *rules, data=None, extract=True, first=True, replace_rule=None, extract_key=False):
        return SpiderExtractor.extractor(self, *rules, data=data or self.resp_data, extract_method='css',
                                         extract=extract, first=first, replace_map=replace_rule,
                                         extract_key=extract_key)

    def xpath(self, *rules, data=None, replace_rule=None, extract_key=False):
        return SpiderExtractor.extractor(self, *rules, data=data or self.resp_data, extract_method='xpath',
                                         replace_map=replace_rule, extract_key=extract_key)

    def init_saver(self, path=None, host=None, port=None, user=None, password=None, database=None, charset=None,
                   **kwargs):
        if not host and not path: path = './scraped.csv'
        SpiderSaver.__init__(self, path=path, host=host, port=port, user=user, password=password, database=database,
                             charset=charset, **kwargs)

    @property
    def url(self):
        return self.path + self.param if self.path else ''

    @url.setter
    def url(self, url):
        self._spider['path'] = self._string_to_dict(url, tag='path')
        self._spider['param'] = self._string_to_dict(url, tag='param')

        if self.headers.get('Host'): self.update('Host', self._spider['path'].get('domain'), tag='header')
        if self.prepare: self.prepared_request_queue.push(self._preparing_request(), 0)

    @property
    def body(self):
        if not self.post_type: return ''

        body = self._spider.get('body')
        if self.post_type == 'form':
            return '&'.join(f'{key}={value}' for key, value in body.items())
        else:
            return json.dumps(body)

    @body.setter
    def body(self, body):
        self._spider['body'] = self._string_to_dict(body, tag='body')
        if self.prepare: self.prepared_request_queue.push(self._preparing_request(), 0)
