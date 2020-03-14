import os
import time
from urllib import request
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

urllib3.disable_warnings()


class WebC(object):
    def __init__(self, url=None, headers=None, cookies={}, timeout=30):
        from fake_useragent import UserAgent
        self._url = url
        self._save = False
        self._encode = 'utf-8'
        self._response = None
        self._cookies = cookies
        self._timeout = timeout
        self._headers = headers
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
        self._response = requests.get(self._url, headers=self._headers, cookies=self._cookies, timeout=self._timeout)
        return self._response

    @property
    def html(self, save_path=None):
        resp = self.response
        resp.encoding = self._char
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
        resp = requests.post(self._url, json=data, headers=self._headers)
        ct = resp.content
        json_dict = json.loads(ct)
        return json_dict
