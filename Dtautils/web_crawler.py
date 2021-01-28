import json
import logging
import re
from parsel import Selector
import requests
from requests import Request, Session
from requests.cookies import merge_cookies, cookiejar_from_dict
from Dtautils.data_factory import Printer, DataGroup, DataIter
from queue import Queue
from threading import Lock

lock = Lock()
logger = logging.getLogger(__name__)


class Spider(object):

    # todo add cookie jar dict
    def __init__(self, url=None, body=None, header=None, cookie=None, overwrite=True, name=None, want=None,
                 post_type=None, tag=None, auto_update_rule=None, **kwargs):

        if not header: header = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}

        self.name = name if name else 'Spider'
        self.method = 'POST' if body else 'GET'
        self.post_type = 'form' if body and not post_type else post_type

        self._path_dict = self.str_to_dict(url, tag='path')
        self._param_dict = self.str_to_dict(url, tag='param')
        self._body_dict = self.str_to_dict(body, tag='body')
        self._header_dict = self.str_to_dict(header, tag='header')
        self.overwrite = overwrite
        self.auto_update_rule = auto_update_rule

        cookie_dict = self.str_to_dict(cookie, tag='cookie')
        self._cookie_jar = cookiejar_from_dict(cookie_dict) if cookie else requests.cookies.RequestsCookieJar()

        self._resp = None
        self.request_kwargs = {}
        self.want = want
        self.kwargs = kwargs
        self.others = None
        self.tag = tag
        self.request_count = 0
        self.session = Session()

        self._prepare_request = Queue()
        self._resp_data = Queue()
        self.request_history = []

        self.prepare_request = Request(url=self.url, data=self.body, headers=self.headers, cookies=self.cookies,
                                       method=self.method).prepare()

    @property
    def url(self):
        return self.path + self.param if self.path else ''

    @url.setter
    def url(self, url):
        self._path_dict = self.str_to_dict(url, tag='path')
        self._param_dict = self.str_to_dict(url, tag='param')

        if self.headers.get('Host'): self.update('Host', self._path_dict.get('domain'), tag='header')

    @property
    def path(self):
        assert self._path_dict, 'Please set a url for Spider'

        protocol = self._path_dict.get('protocol')
        domain = self._path_dict.get('domain')
        sub_path = '/'.join([value for key, value in self._path_dict.items() if key not in ['protocol', 'domain']])
        return f'{protocol}://{domain}/{sub_path}'

    @path.setter
    def path(self, path):
        self._path_dict = self.str_to_dict(path, tag='path')

    @property
    def param(self):
        if not self._param_dict: return ''
        param_str = '&'.join([f'{key}={value}' for key, value in self._param_dict.items()])
        return '?' + param_str

    @param.setter
    def param(self, params):
        self._param_dict = self.str_to_dict(params, tag='param')

    @property
    def body(self):
        if not self.post_type: return ''

        if self.post_type == 'form':
            return '&'.join([f'{key}={value}' for key, value in self._body_dict.items()])
        else:
            return json.dumps(self._body_dict)

    @body.setter
    def body(self, body):
        self._body_dict = self.str_to_dict(body, tag='body')

    @property
    def headers(self):
        return self._header_dict

    @headers.setter
    def headers(self, header):
        self._header_dict = self.str_to_dict(header, tag='header')

    @property
    def cookies(self):
        return self._cookie_jar.get_dict()

    @cookies.setter
    def cookies(self, cookie):
        cookie_dict = self.str_to_dict(cookie, tag='cookie')
        self._cookie_jar = cookiejar_from_dict(cookie_dict=cookie_dict, cookiejar=self._cookie_jar,
                                               overwrite=self.overwrite)

    @property
    def cookie_jar(self):
        return self._cookie_jar

    @property
    def key_dict(self):
        return {
            'path': list(self._path_dict.keys()),
            'param': list(self._param_dict.keys()),
            'body': list(self._body_dict.keys()),
            'header': list(self._header_dict.keys()),
            'cookie': list(self.cookies.keys()),
        }

    @property
    def prepare_request(self):
        return self._prepare_request.get() if not self._prepare_request.empty() else None

    @prepare_request.setter
    def prepare_request(self, req):
        self._prepare_request.put(req)

    @property
    def request_info_failed(self):
        msg = f'Website page downloaded do not content {self.want} ...' if self.want else 'Website page download error ...'
        status = self.status if not self.want else self.status_code
        return f'{msg} {self.url}\nstatus: {status}\n{self.resp_data}'

    @property
    def resp(self):
        if not self._resp: self.request()
        return self._resp

    @resp.setter
    def resp(self, resp):
        self._resp = resp

        if self.status == 200 or self.status == self.want:
            self._resp_data.put(resp.text if '<html' in resp.text and '</html>' in resp.text else resp.json())
        else:
            print(self.request_info_failed)

    @property
    def resp_data(self):
        if self._resp_data.empty(): self.request()
        return self._resp_data.get() if not self._resp_data.empty() else None

    @resp_data.setter
    def resp_data(self, resp_data):
        self._resp_data.put(resp_data)

    @property
    def status(self):
        if not self._resp: self.request()

        if not self.want:
            return self.status_code

        elif isinstance(self.want, str):
            result = re.search(self.want, self._resp.text)
            return result.group() if result else None
        else:
            raise Exception(f'Unsupported want format ... {self.want}')

    @property
    def status_code(self):
        if hasattr(self._resp, 'status_code'): return self._resp.status_code
        if hasattr(self._resp, 'status'): return self._resp.status

    def request(self, **kwargs):
        assert self.url, 'Please set a url for Spider'

        self.request_kwargs = {**self.request_kwargs, **kwargs}

        prepared_request = self.prepare_request
        if prepared_request:
            resp = self.session.send(prepared_request, **self.request_kwargs)
            self.request_count += 1
            self.resp = resp
            return resp
        else:
            msg = 'No prepared request error ... spider prepare request queue is empty, please set prepare True in update method'
            print(msg)

    def find(self, *rules, RE=None, re_mode='search', group_index=1):
        result = DataIter(*rules, data=self.resp_data, mode='search', RE=RE, re_mode=re_mode, group_index=group_index)
        return result.result

    def css(self, *rules, extract=True, first=True, extract_key=False):
        css_tree = Selector(self.resp_data)
        result = {}

        if len(rules) == 1 and isinstance(rules[0], str):
            result = css_tree.css(rules[0])

        elif len(rules) == 1 and isinstance(rules[0], dict):
            for key, css_rule in rules[0].items():
                if extract_key:
                    key = css_tree.css(key)
                    key = key.extract() if not first else key.extract_first()
                result[key] = css_tree.css(css_rule)
        else:
            print(f'Rule Format Error ... unsupported rule format {rules}')

        if extract and isinstance(result, dict):
            for key, value in result.items():
                result[key] = value.extract() if not first else value.extract_first()
        elif extract:
            result = result.extract() if not first else result.extract_first()

        return result

    def update_cookie_from_header(self):
        cookie = self.headers.get('Cookie')
        if cookie:
            cookie_dict = self.str_to_dict(cookie, tag='cookie')
            self.update(cookie_dict, tag='cookie')

    def update(self, *args, tag=None, prepare=False):
        """ update tag use args

        tag: param, body, header, cookie
        args: (dict,) or (str,str) or (list,list) or (dict,dict) or (list,list,dict)
        """
        # auto set tag if tag param is not be provide

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

        if prepare: self.prepare_request = Request(url=self.url, data=self.body, headers=self.headers,
                                                   cookies=self.cookies, method=self.method).prepare()

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
        if self.tag:
            tag = self.tag
        else:
            tag_name_list = [tag_name for tag_name, key_list in self.key_dict.items() if key in key_list]
            assert len(tag_name_list) <= 1, f'Please set tag for update, there are many tag name: {tag_name_list}'

            if tag_name_list:
                tag = tag_name_list[0]
            else:
                tag = 'param' if self.method == 'GET' else 'body'
        return tag

    def str_to_dict(self, string, tag=None):
        """ translate string to dict

        string: url, body, header or cookie
        tag: param, body, header or cookie
        rtype: dict
        """

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
            if self.body: return

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

            # sting : 'name=...'
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
        d_group = DataGroup(name='Params')
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
