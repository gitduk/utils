import os
import time
from urllib import request
import requests
import urllib3
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

urllib3.disable_warnings()


class WebC(object):
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random
    }

    def __init__(self, url):
        from fake_useragent import UserAgent
        self.__ua = UserAgent()
        self.__headers = {
            'User-Agent': self.__ua.random
        }
        self.__url = url
        self.__save = True
        self.__char = 'utf-8'

    @property
    def save(self):
        return self.__save

    @save.setter
    def save(self, value):
        self.__save = value

    @property
    def char(self):
        return self.__char

    @char.setter
    def char(self, char):
        self.__char = char

    @property
    def html(self):
        time.sleep(0.2)
        rq = requests.get(self.__url, headers=self.__headers)
        time.sleep(0.5)
        rq.encoding = self.__char
        html = rq.text
        if self.save:
            with open('result.html', 'w') as f:
                f.write(html)
        return html

    @property
    def header(self):
        response = request.urlopen(self.__url)
        header = response.info()
        return header

    @property
    def soup(self):
        if os.path.exists('result.html'):
            soup = BeautifulSoup(open('result.html'), 'html.parser')
        else:
            soup = BeautifulSoup(self.html, 'html.parser')
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
        driver.implicitly_wait(10)
        driver.get(self.__url)
        return driver

    def selenium_drive_waiter(self, wait_time, locator, option='located', text=None):
        driver = self.selenium_driver
        if option == 'located':
            WebDriverWait(driver, wait_time, 0.5).until(EC.presence_of_element_located(locator))
        elif option == 'all_located':
            WebDriverWait(driver, wait_time, 0.5).until(EC.presence_of_all_elements_located(locator))
        elif option == 'visibility':
            WebDriverWait(driver, wait_time, 0.5).until(EC.visibility_of_element_located(locator))
        elif option == 'text_present':
            WebDriverWait(driver, wait_time, 0.5).until(
                EC.text_to_be_present_in_element(locator, text))
