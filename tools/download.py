import os
import re
import sys
import time
import requests
from tools.log import Logger


class Downloader(object):
    def __init__(self, path, url, name, postfix):
        self._path = path
        self._url = url
        self._name = name
        self._max_retry = 3
        self.postfix = postfix
        self.logger = Logger()

    @property
    def path(self):
        return self._path

    @property
    def url(self):
        return self._url

    @property
    def name(self):
        return self._name

    @property
    def max_retry(self):
        return self._max_retry

    def download_picture(self):
        print('-' * 100)
        self.logger.info('Path: {}'.format(self.path + self.name + self.postfix))
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        r = requests.get(self.url, stream=True)
        with open(self.path + self.name + '.' + self.postfix, 'wb') as f:
            for chunk in r.iter_content(chunk_size=32):
                f.write(chunk)

    def download_video(self):
        print('-' * 100)
        self.logger.info('Path: {}'.format(self.path + self.name + self.postfix))
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
                    self.logger.info("Downloaded! [{:.2f}MB]".format(size / (1024 * 1024)))
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

                with open(self.path + self.name + '.' + self.postfix, 'ab') as file:
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
                self.logger.info("总耗时: " + "{:.2f}".format(end - start) + "秒\n")

                content_offset += resp_length
                if content_offset >= total_length:
                    break

    def run(self):
        max_retry_count = self.max_retry
        retry_count = 0
        while retry_count < max_retry_count:
            try:
                if self.postfix == 'mp4':
                    self.download_video()
                elif self.postfix in ['jpg', 'png']:
                    self.download_picture()
                break
            except Exception as Ex:
                self.logger.warning("[下载异常]\nEX: {}".format(str(Ex)))
                retry_count += 1

        if retry_count == max_retry_count:
            self.logger.warning("[下载失败]")
        else:
            self.logger.info("[下载完成]")

    @path.setter
    def path(self, value):
        self._path = value

    @url.setter
    def url(self, value):
        self._url = value

    @name.setter
    def name(self, value):
        self._name = value

    @max_retry.setter
    def max_retry(self, value):
        self._max_retry = value
