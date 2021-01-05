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

    def __init__(self, url, body_str=None, cookie_str=None):
        self.update_count = 0
        self.url = url if self.update_count == 0 else self.update_url()
        self.body_str = '' if body_str is None else body_str
        self.cookie_str = '' if cookie_str is None else cookie_str
        self.param_dict = {}
        self.cookie_dict = {}
        self.param = None
        self.method = 'POST' if body_str else 'GET'
        self.post_type = 'form' if self.method == 'POST' else ''

        self.all_to_dict()

    # FIXME ...
    def update_url(self):
        if self.method == 'GET' and '?' in self.url:
            path = self.url.split('?')[0]
            get_param_list = []
            for key, value in self.param_dict.items():
                get_param_list.append(f'{key}={value}')
            return path + '?' + '&'.join(get_param_list)
        else:
            return self.url

    def form(self):
        self.param = '&'.join([f'{key}={value}' for key, value in self.param_dict.items()])
        return self.param

    def payload(self):
        self.param = json.dumps(self.param_dict)
        return self.param

    def update(self, key, value):
        self.param_dict[key] = value
        self.update_count += 1

    def update_from_list(self, key_list, value_list):
        for key, value in zip(key_list, value_list):
            self.param_dict[key] = value
        self.update_count += 1

    def update_from_dict(self, update_map):
        for key, value in update_map.items():
            self.param_dict[key] = value
        self.update_count += 1

    def update_from_cookies(self, update_map):
        for key, value in update_map.items():
            self.param_dict[key] = self.cookie_dict.get(value)
        self.update_count += 1

    def all_to_dict(self):

        # process request params
        if '&' in self.body_str:
            self.param_dict = dict([_.split('=') for _ in self.body_str.split('&')])
        elif ':' in self.body_str:
            self.post_type = 'payload'
            self.param_dict = json.loads(self.body_str)
        elif self.body_str == '':
            self.param_dict = dict([_.split('=', 1) for _ in self.url.split('?')[-1].split('&')])
        else:
            self.param_dict = {}
            raise Exception('FIXME ... unexpect body type')

        # process cookie string
        if self.cookie_str == '':
            return None

        for field in self.cookie_str.split(';'):
            keys = self.cookie_dict.keys()

            key = field.split('=', 1)[0].strip()
            value = field.split('=', 1)[1].strip()
            value_in_dict = self.cookie_dict.get(key)
            if key in keys and isinstance(value_in_dict, str):
                self.cookie_dict[key] = [value_in_dict, value]
            elif isinstance(value_in_dict, list):
                self.cookie_dict[key].append(value)
            else:
                self.cookie_dict[key] = value

    def __repr__(self):
        return f'url:{self.url}\nmethod:{self.method} ({self.post_type})\nparam:{self.param_dict}\ncookies:{self.cookie_dict}'


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
