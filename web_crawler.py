# import os
# import json
# import time
#
# import requests
# import urllib3
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# import random
#
# urllib3.disable_warnings()
#
#
# class WebC(object):
#     def __init__(self, url=None, headers=None, cookies=None, proxies=None, timeout=30, ip=False):
#         _headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'
#         }
#         self._url = url
#         self._save = False
#         self._encode = 'utf-8'
#         self._response = None
#         self._timeout = timeout
#         self._headers = headers
#         self._proxies = proxies
#         self._cookies = cookies
#         if not headers:
#             self.headers = _headers
#         if not proxies and ip:
#             self._proxies = self.random_ip
#         if cookies:
#             self.cookies = cookies
#
#     @property
#     def save(self):
#         return self._save
#
#     @save.setter
#     def save(self, value):
#         self._save = value
#
#     @property
#     def encode(self):
#         return self._encode
#
#     @encode.setter
#     def encode(self, char):
#         self._encode = char
#
#     @property
#     def headers(self):
#         return self._headers
#
#     @headers.setter
#     def headers(self, header):
#         self._headers = header
#
#     @property
#     def cookies(self):
#         return self._cookies
#
#     @cookies.setter
#     def cookies(self, cookie_str):
#         cookies_list = cookie_str.split(';')
#         cookie_dict = {}
#         for i in cookies_list:
#             key, val = i.split('=', 1)
#             cookie_dict[key] = val
#         self._cookies = cookie_dict
#
#     @property
#     def session(self):
#         return requests.session()
#
#     @property
#     def response(self):
#         self._response = requests.get(self._url, headers=self._headers, cookies=self._cookies, timeout=self._timeout,
#                                       proxies=self._proxies)
#         return self._response
#
#     @property
#     def html(self, save_path=None):
#         resp = self.response
#         resp.encoding = self.encode
#         html = resp.text
#         if self.save:
#             with open('{}.html'.format(save_path), 'w') as f:
#                 f.write(html)
#         return html
#
#     @property
#     def soup(self):
#         if os.path.exists('result.html'):
#             soup = BeautifulSoup(open('result.html'), 'html.parser')
#         else:
#             soup = BeautifulSoup(self.response.text, 'html.parser')
#         return soup
#
#     @property
#     def selenium_driver(self):
#         # setting
#         chrome_options = Options()
#         chrome_options.add_argument('--headless')
#         chrome_options.add_argument('--disable-gpu')
#         desired_capabilities = DesiredCapabilities.CHROME  # 修改页面加载策略
#         desired_capabilities["pageLoadStrategy"] = "none"  # 注释这两行会导致最后输出结果的延迟，即等待页面加载完成再输出
#         driver = webdriver.Chrome(chrome_options=chrome_options)
#         # driver.implicitly_wait(10)
#         driver.get(self._url)
#         if self._cookies:
#             driver.add_cookie(self._cookies)
#         return driver
#
#     def get_json_dict(self):
#         return json.loads(self.response.content)
#
#     def get_payload_data(self, data):
#         resp = requests.post(self._url, json=data, headers=self._headers, proxies=self._proxies)
#         ct = resp.content
#         json_dict = json.loads(ct)
#         return json_dict
#
#     @property
#     def random_ip(self):
#         time.sleep(0.5)
#         url = 'https://www.xicidaili.com/nn/'
#         web_data = requests.get(url, headers=self._headers)
#         soup = BeautifulSoup(web_data.text, 'html.parser')
#         ips = soup.find_all('tr')
#         ip_list = []
#         for i in range(1, len(ips)):
#             ip_info = ips[i]
#             tds = ip_info.find_all('td')
#             ip_list.append(tds[1].text + ':' + tds[2].text)
#
#         proxy_list = []
#         for ip in ip_list:
#             proxy_list.append('http://' + ip)
#         proxy_ip = random.choice(proxy_list)
#         proxies = {'http': proxy_ip}
#         return proxies
#
#
import inspect
import json
import os
import random
import re
import time
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


def save_html(response, name):
    with open(f"/home/kaige/Github/gov/cn12348/files/{name}.html", "w") as f:
        f.write(response.text)


def retrieve_name(var):
    """
    获取变量名
    """
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    var_name_list = [var_name for var_name, var_val in callers_local_vars if var_val is var]
    if var_name_list:
        return var_name_list[0]
    else:
        raise Exception


def fmt_item(item):
    if item is None:
        return
    else:
        data = item.get("data")
        remote_data_ = item.get("remote_data")
        remote_data = del_dict_depth(remote_data_)
        field_dict = item.get("field_dict")
        value_len_list = [len(str(value)) for key, value in data.items()]
        status = item.get("status")
        changed_dict = item.get("changed_dict")

        try:
            max_length = max(value_len_list) + 2
        except:
            max_length = 10
        else:
            formatter = "{:<25} | {:<20} | {:<8} | {:<%d}" % (max_length + 6)

            print('\n')
            print(formatter.format("key", "db_key", "status", "value"))
            print("-" * (60 + max_length))

            db_map = {"update_time": "update_time", 'source': 'source'}
            for key, value in field_dict.items():
                if "|" in value:
                    for f in value.split("|"):
                        db_map[f] = key
                else:
                    db_map[value] = key

            remote_data["update_time"] = data.get("update_time")
            remote_data["source"] = data.get("source")
            for key, value in remote_data.items():
                db_key = db_map.get(key)
                if db_key == "authority":
                    continue

                db_key = db_key if db_key else ''

                msg = status if db_key else ""
                if status == "UPDATE":
                    msg = status if db_key in [key for key in changed_dict] else ""
                    change_value = changed_dict.get(db_key)
                    value = f"{change_value} --> {value}" if msg else value

                if status == 'ERROR':
                    msg = status

                print(formatter.format(key, db_key, msg, str(value).strip()))

            print("-" * (60 + max_length) + "\n")


def time_to_time(timestamp):
    timeArray = time.localtime(int(timestamp))
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime


def del_dict_depth(data_dict):
    data = {}
    list_data = {}
    for key, value in data_dict.items():
        value = str(value)
        if isinstance(value, dict):
            data = {**data, **del_dict_depth(value)}
        elif isinstance(value, list):
            if not value:
                continue
            if isinstance(value[0], dict):
                list_data[key] = trans_list_to_dict(value)
            else:
                value = '|'.join(value)
            data = {**data, key: value}
        else:
            data = {**data, key: value}

    return {**data, **list_data}


def trans_list_to_dict(data_list):
    result = {}
    for data in data_list:
        for key, value in data.items():
            if key in [_ for _ in result.keys()]:
                value_ = result.get(key)
                result[key] = f'{value_}|{value}'
            else:
                result = {**result, key: value}

    return result


def parse_param_dict(param_dict, parse_key=False, value_index_list=None):
    value_index_list = [0, 1] if value_index_list is None else value_index_list
    if parse_key is True:
        value_index_list.append(-1)

    for key, value in param_dict.items():
        param_list = value.split("|")

        if parse_key:
            param_list.append(key)

        if param_list[1] == '':
            continue

        yield tuple(param_list[index] for index in value_index_list)


def create_field(name):
    create_parse_file = False
    if 'ChinaSpider' in name:
        name = re.search('parse_(.*?)_module_url', name).group(1)
        create_parse_file = True

    with open('spiders/fields/__init__.py', 'r') as f:
        init_content = f.readlines()

    file_path = f'spiders/fields/{name}_fields.py'

    if not os.path.exists(file_path):
        logger.info(f'create file {file_path}')
        with open(file_path, "w") as f:
            f.write(''.join(init_content))

    if create_parse_file:
        path = f'spiders/parse_module/{name}.py'
        if not os.path.exists(path):
            code = """
from cn12348.spiders.parse_module import *
from cn12348.spiders.fields.{}_fields import PERSON_FIELD_DICT, OFFICE_FIELD_DICT

field_tuple = (PERSON_FIELD_DICT, OFFICE_FIELD_DICT)


def level_two(response):
    ...
            """.format(name)
            with open(path, 'w') as f:
                f.write(code)


def create_random_list(num, start=0):
    """
    num: int
    """
    lst = list(range(start, start + num))
    random.shuffle(lst)
    return lst


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



def tran_list_to_dict(L):
    d = {}
    for l in L:
        if '{\n' in l or '}\n' in l or '# \'' in l:
            continue
        if ':' in l:
            key = l.split(':', 1)[0].replace("'", '').replace('\n', '').replace(',', '').replace(' ', '')
            value = l.split(':', 1)[1]
            if '{' in value:
                value = value.replace("'", '').replace('\n', '').replace(' ', '').replace('},', '}')
            else:
                value = value.replace("'", '').replace('\n', '').replace(',', '').replace(' ', '')
            d[key] = value
    return d


def get_fields(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        index_list = []
        num = 0
        start = 0
        for line in lines:
            if '= {' in line:
                start = num
            if '}\n' in line:
                end = num + 1
                index_list.append((start, end))
            num += 1

        person_field_dict = tran_list_to_dict(lines[int(index_list[0][0]):int(index_list[0][1])])
        office_field_dict = tran_list_to_dict(lines[int(index_list[1][0]):int(index_list[1][1])])
        info_keys_dict = tran_list_to_dict(lines[int(index_list[2][0]):int(index_list[2][1])])
        url_map_dict = tran_list_to_dict(lines[int(index_list[3][0]):int(index_list[3][1])])
        body_map_dict = tran_list_to_dict(lines[int(index_list[4][0]):int(index_list[4][1])])
        detail_url_map_dict = tran_list_to_dict(lines[int(index_list[5][0]):int(index_list[5][1])])
        detail_body_map_dict = tran_list_to_dict(lines[int(index_list[6][0]):int(index_list[6][1])])
        result = (
            person_field_dict, office_field_dict, info_keys_dict, url_map_dict, body_map_dict, detail_url_map_dict,
            detail_body_map_dict)

        return result


def replaces(*rep_map_list, target=None, replace_key=False):
    for rep_map in rep_map_list:
        if not isinstance(rep_map, dict):
            values = ['' for _ in rep_map]
            rep_map = dict(zip(list(rep_map), values))
        for k, v in rep_map.items():

            # process target type
            if type(target).__name__ == 'str' and target != '':
                target = target.replace(k, v)
            elif type(target).__name__ == 'list':
                rep_str = '|'.join(target)
                target = rep_str.replace(k, v).split('|')

            # target is a dict
            elif type(target).__name__ == 'dict':
                new_target = {}
                for k_, v_ in target.items():
                    v_ = v_ if v_ else ''
                    if not replace_key:
                        target[k_] = v_.replace(k, v)
                    else:
                        new_key = k_.replace(k, v)
                        new_value = v_.replace(k, v)
                        new_target[new_key] = new_value
                target = new_target

            elif target is None:
                raise Exception('target is None')

    return target
