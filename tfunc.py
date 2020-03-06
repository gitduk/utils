import re
import sys
from urllib import request
import urllib3
import os
import time
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

urllib3.disable_warnings()


def get_time(fmt=None):
    if not fmt:
        fmt = "%Y-%m-%d %H:%M:%S"
    now = int(time.time())
    time_array = time.localtime(now)
    other_style_time = time.strftime(fmt, time_array)
    return other_style_time


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
            print(self.fmt.format(__name__, get_time(), mode, ' ' * (8 - ml), msg))

    def warning(self, msg):
        level = 2
        if level >= self.level:
            mode = self.mode[level - 1]
            ml = len(mode)
            print(self.fmt.format(__name__, get_time(), mode, ' ' * (8 - ml), msg))


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


def picture_downloader(path, pic_url, file_name, pic_type):
    if not os.path.exists(path):
        os.mkdir(path)
    r = requests.get(pic_url, stream=True)
    with open(path + file_name + '.' + pic_type, 'wb') as f:
        for chunk in r.iter_content(chunk_size=32):
            f.write(chunk)


def video_downloader(path, video_url, file_name):
    start = time.time()
    download_header = {
        "Accept-Encoding": "identity;q=1, *;q=0",
        "Range": None,
        "Referer": None,
        # "Connection": "Close",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.59 Safari/537.36 115Browser/8.6.2"
    }
    proxy = {}
    if not os.path.exists(path):
        os.mkdir(path)

    content_offset = 0
    if os.path.exists(path + file_name):
        content_offset = os.path.getsize(path + file_name)

    print('-' * 100)
    print('Path: {}'.format(path + file_name))
    content_length = 1024 * 1024 * 1000
    chunk_size = 1024
    size = content_offset
    total_length = None
    download_header["Referer"] = video_url
    with requests.session() as s:
        s.headers = download_header
        s.proxies = proxy
        s.stream = True
        while True:
            s.headers["Range"] = "bytes=%d-%d" % (content_offset, content_offset + content_length)
            resp = s.get(video_url, timeout=10)
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

            with open(path + file_name, 'ab') as file:
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
