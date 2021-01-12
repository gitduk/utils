import json
import logging
import re
import requests
from requests.cookies import merge_cookies
from utils.data_factory import Printer, DataGroup

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
        self._body_str = '' if body is None else body
        self._param_str = '' if body or '?' not in self._url else self._url.split('?')[-1]
        self._header_str = header if header else 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        self._cookie_str = '' if cookie is None else cookie

        self.method = 'POST' if body else 'GET'
        if self.method == 'POST' and '=' in self._body_str:
            self.post_type = 'form'
        elif self.method == 'POST' and ':' in self._body_str:
            self.post_type = 'payload'
        else:
            self.post_type = ''

        self._cookie_jar_dict = self.cookie_jar._cookies

        self._path_dict = self.str_to_dict(self._path_str, tag='path') if self._path_str else {}
        self._param_dict = self.str_to_dict(self._param_str, tag='param') if self._param_str else {}
        self._body_dict = self.str_to_dict(self._body_str, tag='body') if self._body_str else {}
        self._header_dict = self.str_to_dict(self._header_str, tag='header') if self._header_str else {}
        self._cookie_dict = self.str_to_dict(self._cookie_str, tag='cookie') if self._cookie_str else {}

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
            return self.path + self.param if self.method == 'GET' else self._url
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
        return split_char + '&'.join([f'{key}={value}' for key, value in self._param_dict.items()]) \
            if self.fmt else self._param_dict

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
        return self._header_dict if self._header_dict else ''

    @property
    def cookies(self):
        return self._cookie_dict if self._cookie_dict else ''

    @property
    def cookie_jar(self):
        if not self._cookie_jar.items():
            self._cookie_jar = requests.utils.cookiejar_from_dict(self._cookie_dict)
        else:
            self._cookie_jar = requests.utils.cookiejar_from_dict(self._cookie_dict, self._cookie_jar, self.overwrite)
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
        self._url = url
        self._path_str = self._url.split('?')[0]
        self._param_str = '' if self.body or '?' not in self._url else self._url.split('?')[-1]
        self._path_dict = self.str_to_dict(self._path_str, tag='path')
        self._param_dict = self.str_to_dict(self._param_str, tag='param')

    @path.setter
    def path(self, path):
        if isinstance(path, dict):
            self._path_dict = path
        else:
            raise Exception('Type error ... type of path is not dict')

    @param.setter
    def param(self, params):
        if isinstance(params, dict):
            self._param_dict = params
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

    def cookie_setter(self, string):
        """ build cookie dict use set-cookie field

        string: set-cookie string
        """
        if not string:
            return
        elif string and not isinstance(string, str):
            raise Exception('string is None')

        if isinstance(string, bytes): string = string.decode('utf-8')
        string = re.search('(.*?); Path', string)

        if string:
            string = string.group(1)
            for cookie in string.split(';'):
                if '=' in cookie:
                    key, value = cookie.split('=')[0].strip(), cookie.split('=')[1].strip()
                    self._cookie_dict[key] = value
                else:
                    continue
        else:
            print(f'Set-Cookie filed is None')

    def update(self, *args, tag=None):
        """ update tag use args

        tag: param, body, header, cookie
        args: (dict,) or (str,str) or (list,list) or (dict,dict) or (list,list,dict)
        """
        # auto set tag if tag param is not be provide

        if len(args) == 1 and isinstance(args[0], dict):
            for key, value in args[0].items():
                self._update(key, value, tag)

        elif len(args) == 2 and isinstance(args[0], str):
            key, value = args
            self._update(key, value, tag)

        elif len(args) == 2 and isinstance(args[0], list):
            for key, value in zip(args):
                self._update(key, value, tag)

        elif len(args) == 2 and isinstance(args[0], dict):
            for key, value in args[0].items():
                value = args[1].get(value)
                self._update(key, value, tag)
        elif len(args) == 3 and isinstance(args[0], dict) and isinstance(args[2], dict):
            for key, value in zip(args[0], args[1]):
                value = args[2].get(value)
                self._update(key, value, tag)

    def _update(self, key, value, tag=None):
        if not tag:
            for tag_name, key_list in self.key_dict.items():
                if key in key_list:
                    tag = tag_name
                    break

        if tag == 'param':
            self._param_dict[key] = value
        elif tag == 'body':
            self._body_dict[key] = value
        elif tag == 'header':
            self._header_dict[key] = value
        elif tag == 'cookie':
            self._cookie_dict[key] = value

    def str_to_dict(self, string, tag=None):
        """ translate string to dict

        string: url, body, header or cookie
        tag: param, body, header or cookie
        rtype: dict
        """

        string = string.strip()

        if tag == 'path' and '://' in string:
            protocol = self._path_str.split('://', 1)[0]
            domain = self._path_str.split('://', 1)[1].split('/')[0]
            path_list = self._path_str.split('://', 1)[1].split('/')[1:]
            self._path_dict['protocol'] = protocol
            self._path_dict['domain'] = domain
            self._path_dict = {**self._path_dict, **dict(zip(path_list, path_list))}
            return self._path_dict

        if tag == 'param' and '=' in string:
            self._param_dict = dict([_.split('=', 1) for _ in string.split('&')])
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


url = 'https://www.baidu.com?name=kaige'
url2 = 'https://www.baidu.com?name=dongkai'
ctor = ParamFactory(url)
print(ctor)
ctor.url = url2
print(ctor)
