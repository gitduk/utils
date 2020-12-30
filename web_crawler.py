import os
import json
import time

import requests
import urllib3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import random

urllib3.disable_warnings()


class WebC(object):
    def __init__(self, url=None, headers=None, cookies=None, proxies=None, timeout=30, ip=False):
        _headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'
        }
        self._url = url
        self._save = False
        self._encode = 'utf-8'
        self._response = None
        self._timeout = timeout
        self._headers = headers
        self._proxies = proxies
        self._cookies = cookies
        if not headers:
            self.headers = _headers
        if not proxies and ip:
            self._proxies = self.random_ip
        if cookies:
            self.cookies = cookies

    @property
    def save(self):
        return self._save

    @save.setter
    def save(self, value):
        self._save = value

    @property
    def encode(self):
        return self._encode

    @encode.setter
    def encode(self, char):
        self._encode = char

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, header):
        self._headers = header

    @property
    def cookies(self):
        return self._cookies

    @cookies.setter
    def cookies(self, cookie_str):
        cookies_list = cookie_str.split(';')
        cookie_dict = {}
        for i in cookies_list:
            key, val = i.split('=', 1)
            cookie_dict[key] = val
        self._cookies = cookie_dict

    @property
    def session(self):
        return requests.session()

    @property
    def response(self):
        self._response = requests.get(self._url, headers=self._headers, cookies=self._cookies, timeout=self._timeout,
                                      proxies=self._proxies)
        return self._response

    @property
    def html(self, save_path=None):
        resp = self.response
        resp.encoding = self.encode
        html = resp.text
        if self.save:
            with open('{}.html'.format(save_path), 'w') as f:
                f.write(html)
        return html

    @property
    def soup(self):
        if os.path.exists('result.html'):
            soup = BeautifulSoup(open('result.html'), 'html.parser')
        else:
            soup = BeautifulSoup(self.response.text, 'html.parser')
        return soup

    @property
    def selenium_driver(self):
        # setting
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        desired_capabilities = DesiredCapabilities.CHROME  # 修改页面加载策略
        desired_capabilities["pageLoadStrategy"] = "none"  # 注释这两行会导致最后输出结果的延迟，即等待页面加载完成再输出
        driver = webdriver.Chrome(chrome_options=chrome_options)
        # driver.implicitly_wait(10)
        driver.get(self._url)
        if self._cookies:
            driver.add_cookie(self._cookies)
        return driver

    def get_json_dict(self):
        return json.loads(self.response.content)

    def get_payload_data(self, data):
        resp = requests.post(self._url, json=data, headers=self._headers, proxies=self._proxies)
        ct = resp.content
        json_dict = json.loads(ct)
        return json_dict

    @property
    def random_ip(self):
        time.sleep(0.5)
        url = 'https://www.xicidaili.com/nn/'
        web_data = requests.get(url, headers=self._headers)
        soup = BeautifulSoup(web_data.text, 'html.parser')
        ips = soup.find_all('tr')
        ip_list = []
        for i in range(1, len(ips)):
            ip_info = ips[i]
            tds = ip_info.find_all('td')
            ip_list.append(tds[1].text + ':' + tds[2].text)

        proxy_list = []
        for ip in ip_list:
            proxy_list.append('http://' + ip)
        proxy_ip = random.choice(proxy_list)
        proxies = {'http': proxy_ip}
        return proxies


class ParamFactory(object):
    """
    body_str = 'a=b&c=d&e=f'
    """

    def __init__(self, url, body_str=None):
        self.url = url
        self.body_str = '' if body_str is None else body_str
        self.param_dict = {}
        self.param = None
        self.method = 'POST' if body_str else 'GET'
        self.post_type = 'form' if self.method == 'POST' else ''

        self._to_dict()

    def _to_dict(self):
        if '&' in self.body_str:
            self.param_dict = dict([_.split('=') for _ in self.body_str.split('&')])
        elif ':' in self.body_str:
            self.post_type = 'payload'
            self.param_dict = json.loads(self.body_str)
        else:
            self.param_dict = dict([_.split('=', 1) for _ in self.url.split('?')[-1].split('&')])

    def form(self):
        self.param = '&'.join([f'{key}={value}' for key, value in self.param_dict.items()])
        return self.param

    def payload(self):
        self.param = json.dumps(self.param_dict)
        return self.param

    def update(self, key, value):
        if isinstance(key, str):
            self.param_dict[key] = value
        else:
            for k, v in zip(key, value):
                self.param_dict[k] = v

        if self.body_str == '':
            self.url = self.url.split('?')[0] + '?' + urlencode(self.param_dict)
            return self.url

        else:
            return self.form()

    def __repr__(self):
        return f'url:{self.url}\nmethod:{self.method} ({self.post_type})\nparam:{self.param_dict}'
