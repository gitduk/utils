import re
import sys
from urllib import request
from selenium import webdriver
import urllib3
import os
import time
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from openpyxl import Workbook
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

urllib3.disable_warnings()


class Time(object):
    def __init__(self):
        self.fmt = "%Y-%m-%d %H:%M:%S"
        self.time = time.time()

    @property
    def get_fmt_time(self):
        now = int(time.time())
        time_array = time.localtime(now)
        other_style_time = time.strftime(self.fmt, time_array)
        return other_style_time

    @get_fmt_time.setter
    def get_fmt_time(self, fmt):
        self.fmt = fmt


class Logger(object):
    def __init__(self, level=0):
        self.level = level
        self.fmt = '[{}] [{}] [{}]{}: {}'
        self.mode = ['INFO', 'WARNING']

    def info(self, msg):
        level = 1
        if level >= self.level:
            mode = self.mode[level - 1]
            ml = len(mode)
            print(self.fmt.format(__name__, Time.get_fmt_time, mode, ' ' * (8 - ml), msg))

    def warning(self, msg):
        level = 2
        if level >= self.level:
            mode = self.mode[level - 1]
            ml = len(mode)
            print(self.fmt.format(__name__, Time.get_fmt_time, mode, ' ' * (8 - ml), msg))


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


class Sql(object):

    def __init__(self, user, password, port, dbname, char, base):
        self.engine = create_engine(
            'mysql://{}:{}@localhost:{}/{}?charset={}'.format(user, password, port, dbname, char),
            echo=False)
        self.__Base = base
        self.__Base.metadata.create_all(self.engine)
        self.__Session = sessionmaker(bind=self.engine)
        self.__session = self.__Session()

    def write(self, msg):
        self.__session.add(msg)
        self.__session.commit()

    @property
    def session(self):
        return self.__session


class Downloader(object):
    def __init__(self, path, url, name, _type):
        self.path = path
        self.url = url
        self.name = name
        self.type = _type

    def picture(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        r = requests.get(self.url, stream=True)
        with open(self.path + self.name + '.' + self.type, 'wb') as f:
            for chunk in r.iter_content(chunk_size=32):
                f.write(chunk)

    def video(self):
        start = time.time()
        download_header = {
            "Accept-Encoding": "identity;q=1, *;q=0",
            "Range": None,
            "Referer": None,
            # "Connection": "Close",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.59 Safari/537.36 115Browser/8.6.2"
        }
        proxy = {}
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        content_offset = 0
        if os.path.exists(self.path + self.name):
            content_offset = os.path.getsize(self.path + self.name)

        print('-' * 100)
        print('Path: {}'.format(self.path + self.name))
        content_length = 1024 * 1024 * 1000
        chunk_size = 1024
        size = content_offset
        total_length = None
        download_header["Referer"] = self.url
        with requests.session() as s:
            s.headers = download_header
            s.proxies = proxy
            s.stream = True
            while True:
                s.headers["Range"] = "bytes=%d-%d" % (content_offset, content_offset + content_length)
                resp = s.get(self.url, timeout=10)
                if not resp.ok:
                    print("Downloaded! [{:.2f}MB]".format(size / (1024 * 1024)))
                    if resp.status_code == 416:
                        return
                    continue
                resp_length = int(resp.headers["Content-Length"])
                resp_range = resp.headers["Content-Range"]
                if total_length is None:
                    total_length = int(resp_range.split("/")[1])
                resp_offset = int(re.compile(r"bytes (\d+)-").findall(resp_range)[0])
                if resp_offset != content_offset:
                    continue

                with open(self.path + self.name, 'ab') as file:
                    progress_bar_length = 50
                    for data in resp.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        size += len(data)
                        done = int(progress_bar_length * size / total_length)
                        sys.stdout.write(
                            "\r[{}{}] [{:.2f}MB] [{:.2f}MB]".format('=' * done, ' ' * (progress_bar_length - done),
                                                                    size / chunk_size / 1024,
                                                                    total_length / (1024 * 1024)
                                                                    # str(round(float(size / total_length) * 100, 2)), # %
                                                                    ))
                        sys.stdout.flush()

                end = time.time()
                print(" 总耗时: " + "{:.2f}".format(end - start) + "秒\n")

                content_offset += resp_length
                if content_offset >= total_length:
                    break


class Excel(object):
    def __init__(self, path):
        self.wb = Workbook()
        self.sheet = self.wb.active
        self.path = path + '.xlsx'

    def write_head(self, head_tag_list, head_title_list):
        head_tag_list = list(head_tag_list)
        for i, h in enumerate(head_title_list):
            self.sheet[head_tag_list[i] + '1'] = h
        self.wb.save(self.path)

    def save(self):
        self.wb.save(self.path)
