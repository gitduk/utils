import json
import re
import logging

import requests

logger = logging.getLogger(__name__)


class ParamFactory(object):
    """
    Process requests params and cookies
    """

    def __init__(self, url, body_str=None, header_str=None, cookie_str=None, overwrite=True):
        self._url = url
        self._body_str = '' if body_str is None else body_str
        self._param = ''
        self._param_dict = {}

        self._header_str = '' if header_str is None else header_str
        self._cookie_str = '' if cookie_str is None else cookie_str
        self._header_dict = {}
        self._cookie_dict = {}
        self._cookie_jar = requests.cookies.RequestsCookieJar()

        self.method = 'POST' if body_str else 'GET'
        self.post_type = 'form' if self.method == 'POST' else ''
        self.path = self._url.split('?')[0]

        self.overwrite = overwrite
        self.update_status = 0
        self._init_all()

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

    def _init_all(self):
        # init param
        if self.method == 'POST':
            self.body_to_dict()
        else:
            self.url_param_to_dict()

        # init header
        if self._header_str != '':
            self.trans_to_dict(to='header')

        # init cookie
        if self._cookie_str != '':
            self.trans_to_dict(to='cookie')

    @property
    def url(self):
        if self.method == 'GET' and '?' in self._url:
            return self.path + '?' + '&'.join([f'{key}={value}' for key, value in self._param_dict.items()])
        else:
            return self._url

    @property
    def param(self):
        """
        param for request
        """
        if self.method == 'POST' and self.post_type == 'form':
            return '&'.join([f'{key}={value}' for key, value in self._param_dict.items()])
        elif self.method == 'POST' and self.post_type == 'payload':
            return json.dumps(self._param_dict)
        else:
            return '?' + '&'.join([f'{key}={value}' for key, value in self._param_dict.items()])

    @property
    def header(self):
        return self._header_dict

    @property
    def cookie(self):
        return self._cookie_dict

    @property
    def cookie_jar(self):
        if not self._cookie_jar.items():
            self._cookie_jar = requests.utils.cookiejar_from_dict(self._cookie_dict)
        else:
            self._cookie_jar = requests.utils.cookiejar_from_dict(self._cookie_dict, self._cookie_jar, self.overwrite)
        return self._cookie_jar

    def cookie_setter(self, string):
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

    def update(self, key, value, tag='param'):
        if tag == 'param':
            self._param_dict[key] = value
        elif tag == 'header':
            self._header_dict[key] = value
        elif tag == 'cookie':
            self._cookie_dict[key] = value

    def update_from_list(self, key_list, value_list, tag='param'):
        for key, value in zip(key_list, value_list):
            if tag == 'param':
                self._param_dict[key] = value
            elif tag == 'header':
                self._header_dict[key] = value
            elif tag == 'cookie':
                self._cookie_dict[key] = value

    def update_from_dict(self, update_map, target_map=None, tag='param'):

        for key, value in update_map.items():
            if target_map is None:
                real_value = value
            else:
                real_value = target_map.get(value)

            if tag == 'param':
                self._param_dict[key] = real_value if real_value else ''
            elif tag == 'header':
                self._header_dict[key] = real_value if real_value else ''
            elif tag == 'cookie':
                self._cookie_dict[key] = real_value if real_value else ''

    def update_from_cookies(self, update_map):
        for key, value in update_map.items():
            self._param_dict[key] = self._cookie_dict.get(value)

    def body_to_dict(self, body=None):
        body = body if body else self._body_str
        if '=' in body and '&' in body:
            self._param_dict = dict([_.split('=', 1) for _ in body.split('&')])
        elif '=' in body:
            self._param_dict = dict([body.split('=')])
        elif ':' in body:
            self.post_type = 'payload'
            self._param_dict = json.loads(body)

    def url_param_to_dict(self, url=None):
        url = url if url else self._url
        if '?' in url:
            self._param_dict = dict([_.split('=', 1) for _ in url.split('?')[-1].split('&')])
        # else:
        #     raise Exception('GET method with no "?"')

    def trans_to_dict(self, string=None, to=None):

        if string is None:
            string = self._header_str.strip() if to == 'header' else self._cookie_str.strip()

        if to == 'cookie':
            split_params = [';', '=']
        elif to == 'header':
            split_params = ['\n', ':']
        elif ';' in string and '=' in string and ':' in string:
            split_params = ['\n', ':']
        else:
            split_params = [';', '=']

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

        if to == 'header':
            self._header_dict = target_dict
        elif to == 'cookie':
            self._cookie_dict = target_dict

        return target_dict

    def __repr__(self):
        return "url: {}\nparam: {}\nheaders: {}\ncookies: {}\n".format(self.url, self.param, self.header, self.cookie)
