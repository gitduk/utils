import json
import logging

import urllib3
from parsel import Selector
import requests
from requests import Request, Session
from requests.cookies import merge_cookies, cookiejar_from_dict
from Dtautils.data_factory import Printer, DataGroup, DataIter
from queue import Queue

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class SpiderUpdater(object):
    UA = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}

    def __init__(self, url=None, body=None, header=None, cookie=None, overwrite=True):

        if not header: header = self.UA

        self.method = 'POST' if body else 'GET'
        self.post_type = None
        if body: self.post_type = 'form' if '=' in body else 'payload'

        self._path_dict = self._string_to_dict(url, tag='path')
        self._body_dict = self._string_to_dict(body, tag='body')
        self._param_dict = self._string_to_dict(url, tag='param')
        self._header_dict = {**self.UA, **self._string_to_dict(header, tag='header')}
        self.overwrite = overwrite

        cookie_dict = self._string_to_dict(cookie, tag='cookie')
        self._cookie_jar = cookiejar_from_dict(cookie_dict) if cookie else requests.cookies.RequestsCookieJar()

    @property
    def url(self):
        return self.path + self.param if self.path else ''

    @url.setter
    def url(self, url):
        self._path_dict = self._string_to_dict(url, tag='path')
        self._param_dict = self._string_to_dict(url, tag='param')

        if self.headers.get('Host'): self.update('Host', self._path_dict.get('domain'), tag='header')

    @property
    def path(self):
        assert self._path_dict, 'Please set a url for Spider'

        protocol = self._path_dict.get('protocol')
        domain = self._path_dict.get('domain')
        sub_path = '/'.join([value for key, value in self._path_dict.items() if key not in ['protocol', 'domain']])
        return f'{protocol}://{domain}/{sub_path}'

    @property
    def path_dict(self):
        return self._path_dict

    @path.setter
    def path(self, path):
        self._path_dict = self._string_to_dict(path, tag='path')

    @property
    def param(self):
        if not self._param_dict: return ''
        param_str = '&'.join([f'{key}={value}' for key, value in self._param_dict.items()])
        return '?' + param_str

    @property
    def param_dict(self):
        return self._param_dict

    @param.setter
    def param(self, params):
        self._param_dict = self._string_to_dict(params, tag='param')

    @property
    def body(self):
        if not self.post_type: return ''

        if self.post_type == 'form':
            return '&'.join([f'{key}={value}' for key, value in self._body_dict.items()])
        else:
            return json.dumps(self._body_dict)

    @property
    def body_dict(self):
        return self._body_dict

    @body.setter
    def body(self, body):
        self._body_dict = self._string_to_dict(body, tag='body')

    @property
    def headers(self):
        return self._header_dict

    @headers.setter
    def headers(self, header):
        self._header_dict = self._string_to_dict(header, tag='header')

    @property
    def cookies(self):
        return self._cookie_jar.get_dict()

    @cookies.setter
    def cookies(self, cookie):
        cookie_dict = self._string_to_dict(cookie, tag='cookie')
        self._cookie_jar = cookiejar_from_dict(cookie_dict=cookie_dict, cookiejar=self._cookie_jar,
                                               overwrite=self.overwrite)

    @property
    def cookie_jar(self):
        return self._cookie_jar

    @property
    def _key_dict(self):
        return {
            'path': list(self._path_dict.keys()),
            'param': list(self._param_dict.keys()),
            'body': list(self._body_dict.keys()),
            'header': list(self._header_dict.keys()),
            'cookie': list(self.cookies.keys()),
        }

    def update_cookie_from_header(self):
        cookie = self.headers.get('Cookie')
        if cookie:
            cookie_dict = self._string_to_dict(cookie, tag='cookie')
            self.update(cookie_dict, tag='cookie')

    def update(self, *args, tag=None, prepare=False):
        """ update tag use args

        tag: param, body, header, cookie
        args: (dict,) or (str,str) or (list,list) or (dict,dict) or (list,list,dict)
        """

        if len(args) == 1 and isinstance(args[0], dict):
            for key, value in args[0].items():
                self._update(key, value, tag=tag)

        elif len(args) == 1 and isinstance(args[0], requests.models.Response):
            self._cookie_jar.update(args[0].cookies)

        elif len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], str):
            key, value = args
            self._update(key, value, tag=tag)

        elif len(args) == 2 and isinstance(args[0], list) and isinstance(args[1], list):
            for key, value in zip(args):
                self._update(key, value, tag=tag)

        elif len(args) == 2 and isinstance(args[0], dict) and isinstance(args[1], dict):
            for key, value in args[0].items():
                value = args[1].get(value)
                self._update(key, value, tag=tag)

        elif len(args) == 3 and isinstance(args[0], list) and isinstance(args[1], list) and isinstance(args[2], dict):
            for key, value in zip(args[0], args[1]):
                value = args[2].get(value)
                self._update(key, value, tag=tag)
        else:
            raise Exception(f'Update Error ... unsupported update args {args}')

        if prepare: return Request(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                   method=self.method).prepare()

    def _update(self, key, value, tag=None):
        if not tag: tag = self._get_tag(key)

        if tag == 'param':
            self._param_dict[key] = value
        elif tag == 'body':
            self._body_dict[key] = value
        elif tag == 'header':
            self._header_dict[key] = value
        elif tag == 'cookie':
            self._cookie_jar.set(key, value)
        elif tag == 'path':
            self._path_dict[key] = value
        else:
            print(f'Update faild ... no tag {key}:{value}')

    def _get_tag(self, key):
        tag_name_list = [tag_name for tag_name, key_list in self._key_dict.items() if key in key_list]
        assert len(tag_name_list) <= 1, f'Please set tag for update, there are many tag name: {tag_name_list}'

        if tag_name_list:
            tag = tag_name_list[0]
        else:
            tag = 'param' if self.method == 'GET' else 'body'
        return tag

    def _string_to_dict(self, string, tag=None):
        result = {}
        if not string: return result
        if isinstance(string, dict): return string

        string = string.strip()

        if tag == 'path' and '://' in string:
            if '?' in string: string = string.split('?')[0]

            protocol = string.split('://', 1)[0]
            domain = string.split('://', 1)[1].split('/')[0]
            path_list = string.split('://', 1)[1].split('/')[1:]

            result['protocol'] = protocol
            result['domain'] = domain
            result = {**result, **dict(zip([str(i + 1) for i in range(len(path_list))], path_list))}

        if tag == 'param':
            if self.body: return result

            # sting : 'https://...?...'
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

            if tag == 'header': self._header_dict = result
            if tag == 'cookie': self._cookie_jar = cookiejar_from_dict(result)

        return result

    def preview(self, tag=None):
        d_group = DataGroup('Spider')
        d_group.add_info('url', self.url)
        d_group.add_info('param', self.param)
        d_group.add_info('body', self.body)

        preview_dict = {'headers': self.headers, 'cookies': self.cookies}
        preview_list = ['headers', 'cookies'] if not tag else [tag]

        for key, value in preview_dict.items():
            if key in preview_list:
                d_group.add_data(key, value)
            else:
                continue

        printer = Printer()
        return printer.parse_data_group(d_group)

    def __repr__(self):
        lines = self.preview()
        return '\n'.join(lines)


class SpiderExtractor(object):
    def find(self, *rules, data=None, match_mode=None, re_mode='search', group_index=None):
        result = DataIter(*rules, data=data, mode='search', match_mode=match_mode, re_mode=re_mode,
                          group_index=group_index)
        return result.result

    def css(self, *rules, data=None, extract=True, first=True, extract_key=False):

        css_tree = Selector(data)
        result = {}

        if len(rules) == 1 and isinstance(rules[0], str):
            result = self._get_css_result(css_tree, rules[0])

        elif len(rules) == 1 and isinstance(rules[0], dict):
            for key, css_rule in rules[0].items():
                if extract_key:
                    key = self._get_css_result(css_tree, key)
                    key = key.extract() if not first else key.extract_first()
                result[key] = self._get_css_result(css_tree, css_rule)
        else:
            print(f'Rule Format Error ... unsupported rule format {rules}')

        if extract and isinstance(result, dict):
            for key, value in result.items():
                result[key] = self._extract_selector(value, first=first)
        elif extract:
            result = self._extract_selector(result, first=first)

        return result

    @staticmethod
    def _extract_selector(value, first=None):
        if hasattr(value, 'extract'):
            return value.extract() if not first else value.extract_first()
        else:
            value = [_.extract() if not first else _.extract_first() for _ in value if _.extract()]
            return value[0] if len(value) == 1 else value

    @staticmethod
    def _get_css_result(css_tree, css_rule):
        if '|' not in css_rule:
            result = css_tree.css(css_rule)
        else:
            result = [css_tree.css(_) for _ in css_rule.split('|')]
        return result


class SpiderDownloader(object):
    def __init__(self, timeout=10, stream=False, verify=None, allow_redirects=True, proxies=None, hooks=None,
                 cert=None):
        self.download_count = 0
        self.session = Session()
        self._prepare_request_queue = Queue()
        self._resp_queue = Queue()
        self.response = None

        self.timeout = timeout
        self.stream = stream
        self.verify = verify
        self.allow_redirects = allow_redirects
        self.proxies = proxies
        self.hooks = hooks
        self.cert = cert

    @property
    def prepare_request(self):
        return self._prepare_request_queue.get() if not self._prepare_request_queue.empty() else None

    @prepare_request.setter
    def prepare_request(self, req):
        self._prepare_request_queue.put(req)

    @property
    def resp(self):
        if self._resp_queue.empty():
            self.response = self.request()
        else:
            self.response = self._resp_queue.get()
        return self.response if not self._resp_queue.empty() else None

    @resp.setter
    def resp(self, resp):
        self._resp_queue.put(resp)

    @property
    def count(self):
        return {'req': self._prepare_request_queue.qsize(), 'resp': self._resp_queue.qsize(),
                'download': self.download_count}

    def request(self, **kwargs):
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
            return resp
        else:
            print('No prepared request error ... spider prepare request queue is empty!')


class Spider(SpiderUpdater, SpiderDownloader, SpiderExtractor):
    def __init__(self, url=None, body=None, header=None, cookie=None, overwrite=True, timeout=10, stream=False,
                 verify=None, allow_redirects=True, proxies=None, cert=None):

        super(Spider, self).__init__(url=url, body=body, header=header, cookie=cookie, overwrite=overwrite)

        SpiderDownloader.__init__(self, timeout=timeout, stream=stream, verify=verify, allow_redirects=allow_redirects,
                                  proxies=proxies, cert=cert)

        prepare_request = Request(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                  method=self.method).prepare()
        self._prepare_request_queue.put(prepare_request)

    def update(self, *args, tag=None, prepare=False):
        prepared_request = SpiderUpdater.update(self, *args, tag=tag, prepare=prepare)
        if prepare:
            self._prepare_request_queue.put(prepared_request)

    def find(self, *rules, data=None, match_mode=None, re_mode='search', group_index=None):
        if not data: data = self.get_data()

        return SpiderExtractor.find(self, *rules, data=data, match_mode=match_mode, re_mode=re_mode,
                                    group_index=group_index)

    def css(self, *rules, data=None, extract=True, first=True, extract_key=False):
        if not data: data = self.get_data()
        return SpiderExtractor.css(self, *rules, data=data, extract=extract, first=first, extract_key=extract_key)

    def get_data(self):
        resp = self.resp
        data = resp.text
        if data:
            if '<html' not in data and '</html>' not in data: data = json.loads(data)
        else:
            print(f'response body is empty!\n{resp}')

        return data
