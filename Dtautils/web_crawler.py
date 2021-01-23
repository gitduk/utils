import json
import logging
import requests
from requests.cookies import merge_cookies
from .data_factory import Printer, DataGroup

logger = logging.getLogger(__name__)


class ParamFactory(object):
    """
    Process requests params
    """

    # todo add cookie jar dict
    def __init__(self, url, body=None, header=None, cookie=None, overwrite=True, fmt=True):
        self._url = url
        self._path_dict = {}
        self._param_dict = {}
        self._body_dict = {}
        self._header_dict = {}
        self._cookie_dict = {}
        self.overwrite = overwrite
        self._cookie_jar = requests.cookies.RequestsCookieJar()
        self.fmt = fmt
        self.others = None

        self._path_str = self._url.split('?')[0]
        self._param_str = '' if body or '?' not in self._url else self._url.split('?')[-1]
        self._body_str = body or ''
        self._header_str = header or 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        self._cookie_str = cookie or ''

        self.method = 'POST' if body else 'GET'
        if self.method == 'POST' and '=' in self._body_str:
            self.post_type = 'form'
        elif self.method == 'POST' and ':' in self._body_str:
            self.post_type = 'payload'
        else:
            self.post_type = ''

        self._path_dict = self.str_to_dict(self._url, tag='path') or {}
        self._param_dict = self.str_to_dict(self._url, tag='param') or {}
        self._body_dict = self.str_to_dict(self._body_str, tag='body') or {}
        self._header_dict = self.str_to_dict(self._header_str, tag='header') or {}
        self._cookie_dict = self.str_to_dict(self._cookie_str, tag='cookie') or {}

    def clear(self, key=None):
        if key == 'path':
            self._path_dict.clear()
        elif key == 'param':
            self._param_dict.clear()
        elif key == 'header':
            self._header_dict.clear()
        elif key == 'cookie':
            self._cookie_dict.clear()
        elif key == 'cookie_jar' and self._cookie_jar:
            self._cookie_jar.clear()
        elif key is None:
            self._path_dict.clear()
            self._param_dict.clear()
            self._header_dict.clear()
            self._cookie_dict.clear()
            self._cookie_jar.clear()

    # --------------------------------------------------------------------------------- property
    @property
    def url(self):
        if self.fmt:
            path = self.path[:-1] if self.path.endswith('/') else self.path
            return path + self.param if self.method == 'GET' else self._url
        else:
            return {'path': self.path, 'param': self.param} if self.method == 'GET' else self.path

    @property
    def path(self):
        protocol = self._path_dict.get('protocol')
        domain = self._path_dict.get('domain')
        sub_path = '/'.join([value for key, value in self._path_dict.items() if key not in ['protocol', 'domain']])
        return f'{protocol}://{domain}/{sub_path}' if self.fmt else self._path_dict

    @property
    def param(self):
        split_char = '?' if self._param_dict else ''
        param_str = '&'.join([f'{key}={value}' for key, value in self._param_dict.items()]) if self._param_dict else ''
        return split_char + param_str if self.fmt else self._param_dict

    @property
    def body(self):
        if not self.fmt:
            return self._body_dict
        elif self.post_type == 'form':
            return '&'.join([f'{key}={value}' for key, value in self._body_dict.items()])
        elif self.post_type == 'payload':
            return json.dumps(self._body_dict)
        else:
            return ''

    @property
    def headers(self):
        return self._header_dict if self._header_dict else {}

    @property
    def cookies(self):
        self._cookie_dict = self._cookie_jar.get_dict()
        return self._cookie_dict

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
            'cookie': list(self._cookie_dict.keys()),
        }

    # --------------------------------------------------------------------------------- setter
    @url.setter
    def url(self, url):
        self._path_dict = self.str_to_dict(url, tag='path')
        self._param_dict = self.str_to_dict(url, tag='param')

        if self.headers.get('Host'): self.update('Host', self._path_dict.get('domain'), tag='header')

    @path.setter
    def path(self, path):
        if isinstance(path, dict):
            self._path_dict = path
        elif isinstance(path, str):
            self._path_dict = self.str_to_dict(path, tag='path')
        else:
            raise Exception('Type error ... type of path is not dict or str')

    @param.setter
    def param(self, params):
        if isinstance(params, dict):
            self._param_dict = params
        elif isinstance(params, str):
            self._param_dict = self.str_to_dict(params, tag='param')
        else:
            raise Exception('Type error ... type of params is not dict')

    @body.setter
    def body(self, body):
        if isinstance(body, dict):
            self._body_dict = body
        else:
            raise Exception('Type error ... type of body is not dict')

    @headers.setter
    def headers(self, header):
        if isinstance(header, dict):
            self._header_dict = header
        else:
            raise Exception('Type error ... type of header is not dict')

    @cookies.setter
    def cookies(self, cookie):
        if isinstance(cookie, dict):
            self._cookie_dict = cookie
        else:
            raise Exception('Type error ... type of cookie is not dict')

    # --------------------------------------------------------------------------------- core functions
    def update(self, *args, tag=None):
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

        elif len(args) == 2 and isinstance(args[0], str):
            key, value = args
            self._update(key, value, tag=tag)

        elif len(args) == 2 and isinstance(args[0], list):
            for key, value in zip(args):
                self._update(key, value, tag=tag)

        elif len(args) == 2 and isinstance(args[0], dict):
            for key, value in args[0].items():
                value = args[1].get(value)
                self._update(key, value, tag=tag)
        elif len(args) == 3 and isinstance(args[0], list) and isinstance(args[2], dict):
            for key, value in zip(args[0], args[1]):
                value = args[2].get(value)
                self._update(key, value, tag=tag)

    def _update(self, key, value, tag=None):
        if not tag:
            for tag_name, key_list in self.key_dict.items():
                if key in key_list:
                    tag = tag_name
                    break
        if not tag:
            tag = 'param' if self.method == 'GET' else 'body'

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

    def str_to_dict(self, string, tag=None):
        """ translate string to dict

        string: url, body, header or cookie
        tag: param, body, header or cookie
        rtype: dict
        """

        if not string: return None
        if tag == 'path' and self._path_dict: self._path_dict.clear()
        if tag == 'param' and self._param_dict: self._param_dict.clear()
        if tag == 'header' and self._header_dict: self._header_dict.clear()
        if tag == 'cookie' and self._cookie_dict: self._cookie_dict.clear()

        string = string.strip()

        if tag == 'path' and '://' in string:
            if '?' in string: string = string.split('?')[0]

            protocol = string.split('://', 1)[0]
            domain = string.split('://', 1)[1].split('/')[0]
            path_list = string.split('://', 1)[1].split('/')[1:]

            self._path_dict['protocol'] = protocol
            self._path_dict['domain'] = domain
            self._path_dict = {**self._path_dict, **dict(zip([str(i + 1) for i in range(len(path_list))], path_list))}
            return self._path_dict

        if tag == 'param':
            if self.body: return

            # sting : 'https://...?...'
            if '?' in string:
                if '=' in string:
                    string = string.split('?')[-1]
                    self._param_dict = dict(
                        [_.split('=', 1) for _ in string.split('&') if '=' in _ and not _.endswith('=')])
                    self._param_dict = {**self._param_dict, **dict([(_.strip('='), '') for _ in string.split('&')
                                                                    if _.endswith('=') or '=' not in _])}
                else:
                    self._param_dict = dict([(string, string) for _ in string.split('&')])

            # sting : 'name=...'
            elif '=' in string:
                self._param_dict = dict([_.split('=', 1) for _ in string.split('&')])
            else:
                self._param_dict = {}

            return self._param_dict

        if tag == 'body':
            if '=' in string and '&' in string:
                self._body_dict = dict([_.split('=', 1) for _ in string.split('&')])
            elif '=' in string:
                self._body_dict = dict([string.split('=')])
            elif ':' in string:
                self._body_dict = json.loads(string)
            return self._body_dict

        if tag == 'header' or tag == 'cookie':
            split_params = ['\n', ':'] if tag == 'header' else [';', '=']
            target_dict = {}
            for field in string.split(split_params[0]):
                keys = target_dict.keys()

                key, value = field.split(split_params[1], 1)
                key, value = [key.strip(), value.strip()]

                value_in_dict = target_dict.get(key)
                if key in keys and isinstance(value_in_dict, str):
                    target_dict[key] = [value_in_dict, value]
                elif isinstance(value_in_dict, list):
                    target_dict[key].append(value)
                else:
                    target_dict[key] = value

            if tag == 'header': self._header_dict = target_dict
            if tag == 'cookie': self._cookie_dict = target_dict
            return target_dict

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
