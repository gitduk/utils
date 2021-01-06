import json
import re
import logging

import requests

logger = logging.getLogger(__name__)


class ParamFactory(object):
    """
    Process requests params
    """

    def __init__(self, url, body=None, headers=None, cookies=None, overwrite=True):
        self._url = url
        self._path = self._url.split('?')[0]
        self._param_str = self._url.split('?')[-1]
        self._body_str = '' if body is None else body
        self._header_str = '' if headers is None else headers
        self._cookie_str = '' if cookies is None else cookies

        self._param_dict = {}
        self._body_dict = {}
        self._header_dict = {}
        self._cookie_dict = {}
        self._cookie_jar = requests.cookies.RequestsCookieJar()

        self.method = 'POST' if body else 'GET'
        self.post_type = 'form' if self.method == 'POST' else ''

        self.overwrite = overwrite

        if self._param_str: self.str_to_dict(self._param_str, tag='param')
        if self._body_str: self.str_to_dict(self._body_str, tag='body')
        if self._header_str: self.str_to_dict(self._header_str, tag='header')
        if self._cookie_str: self.str_to_dict(self._cookie_str, tag='cookie')

    def clear(self, key=None):
        if key == 'param':
            self._param_dict.clear()
        elif key == 'header':
            self._header_dict.clear()
        elif key == 'cookie':
            self._cookie_dict.clear()
        elif key == 'cookie_jar' and self._cookie_jar:
            self._cookie_jar.clear()
        elif key is None:
            self._param_dict.clear()
            self._header_dict.clear()
            self._cookie_dict.clear()
            self._cookie_jar.clear()

    @property
    def url(self):
        self._url = self._path + self.param
        return self._url

    @property
    def param(self):
        return '?' + '&'.join([f'{key}={value}' for key, value in self._param_dict.items()])

    @property
    def body(self):
        if self.post_type == 'form':
            return '&'.join([f'{key}={value}' for key, value in self._body_dict.items()])
        elif self.post_type == 'payload':
            return json.dumps(self._body_dict)

    @property
    def headers(self):
        return self._header_dict

    @property
    def cookies(self):
        return self._cookie_dict

    @property
    def cookie_jar(self):
        if not self._cookie_jar.items():
            self._cookie_jar = requests.utils.cookiejar_from_dict(self._cookie_dict)
        else:
            self._cookie_jar = requests.utils.cookiejar_from_dict(self._cookie_dict, self._cookie_jar, self.overwrite)
        return self._cookie_jar

    def cookie_setter(self, string):
        """ build cookie dict use set-cookie field

        string: set-cookie string
        """
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

    def _update(self, key, value, tag=None):
        if tag == 'param':
            self._param_dict[key] = value
        elif tag == 'body':
            self._body_dict[key] = value
        elif tag == 'header':
            self._header_dict[key] = value
        elif tag == 'cookie':
            self._cookie_dict[key] = value

    def update(self, *args, tag='body'):
        """ update tag use args

        tag: param, body, header, cookie
        args: (dict,) or (str,str) or (list,list) or (dict,dict) or (list,list,dict)
        """
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

    def str_to_dict(self, string, tag=None):
        """ translate string to dict

        string: url, body, header or cookie
        tag: param, body, header or cookie
        rtype: dict
        """

        string = string.strip()

        if tag == 'param':
            if '?' in string and '=' in string:
                self._param_dict = dict([_.split('=', 1) for _ in string.split('?')[-1].split('&')])

        if tag == 'body':
            if '=' in string and '&' in string:
                self._body_dict = dict([_.split('=', 1) for _ in string.split('&')])
            elif '=' in string:
                self._body_dict = dict([string.split('=')])
            elif ':' in string:
                self.post_type = 'payload'
                self._body_dict = json.loads(string)

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

    def __repr__(self):
        return "url: {}\nparam: {}\nheaders: {}\ncookies: {}\n".format(self.url, self.body, self.headers, self.cookies)
