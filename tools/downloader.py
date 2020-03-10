import os
import re
import sys
import time
import requests
from tools.logger import Logger
from tools.multithread import ThreadPool
import urllib3
import traceback

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Downloader(object):
    def __init__(self, path, url, name, postfix):
        self._path = path
        self._url = url
        self._name = name.strip().strip('.mp4')
        self._max_retry = 3
        self.postfix = postfix
        self.logger = Logger()

    def __repr__(self):
        return '{}|{}|{}'.format(self.name, self.postfix, self.url)

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
        self.logger.info('Path: {}'.format(self.path + self.name + self.postfix))
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        r = requests.get(self.url, stream=True)
        with open(self.path + self.name + '.' + self.postfix, 'wb') as f:
            for chunk in r.iter_content(chunk_size=32):
                f.write(chunk)

    def download_video(self):
        # print('\n' + '-' * 100)
        start = time.time()
        _file_path = '{}[✴]{}.{}'.format(self.path, self.name, self.postfix)
        file_path = '{}{}.{}'.format(self.path, self.name, self.postfix)

        if os.path.exists(file_path):
            file_size = os.path.getsize(self.path + self.name + '.' + self.postfix)
            self.logger.info("File Downloaded {:.2f}MB {}".format(file_size / (1024 * 1024), self.name))
            return

        with requests.session() as req:
            req.stream = True
            req.verify = False
            req.timeout = 10
            req.headers = {
                "Accept-Encoding": "identity;q=1, *;q=0",
                "Range": None,
                "Referer": self.url,
                # "Connection": "Close",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.59 Safari/537.36 115Browser/8.6.2"
            }
            # ================================================= first request get total length
            resp = req.get(self.url)
            total_length = int(resp.headers['Content-Length'])

            # deal whit invaild url
            if total_length == 0:
                self.logger.warning('Invalid Url! {}'.format(self.name))
                return

            content_offset = 0
            if os.path.exists(_file_path):
                content_offset = os.path.getsize(_file_path)
                self.logger.info(
                    'Continue To Download {:.2f}MB/{:.2f}MB {}'.format(content_offset / (1024 * 1024),
                                                                         total_length / (1024 * 1024), self.name))
            else:
                self.logger.info("Start To Download {:.2f}MB {}".format(total_length / (1024 * 1024), self.name))

            # =================================================== second request with head to download the remain data
            req.headers = {'Range': "bytes=%d-%d" % (content_offset, content_offset + total_length)}
            resp = req.get(self.url)
            chunk_size = 1024
            size = content_offset
            with open(_file_path, 'ab') as file:
                progress_bar_length = 50
                for data in resp.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    size += len(data)
                    done = int(progress_bar_length * size / total_length)
                    sys.stdout.write(
                        "\r[{}{}] [{:.2f}MB] [{:.2f}MB] [{}]".format('=' * done, ' ' * (progress_bar_length - done),
                                                                     size / chunk_size / 1024,
                                                                     total_length / (1024 * 1024),
                                                                     self.name
                                                                     # str(round(float(size / total_length) * 100, 2)), # %
                                                                     ))
                    sys.stdout.flush()
            os.rename(_file_path, file_path)
            end = time.time()
            self.logger.info(
                "下载完成|大小:{:.2f}MB 耗时: {:.2f}秒 文件名:{}".format(total_length / (1024 * 1024), end - start, self.name))

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
                self.logger.error()
                retry_count += 1

        if retry_count == max_retry_count:
            self.logger.warning("下载失败")
        else:
            self.logger.info("下载结束")

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


class Download_from_file(object):
    def __init__(self, file_path, save_path, info=True):
        self.file_path = file_path
        self.save_path = save_path
        self.info = info

    @property
    def download_project_list(self):
        project_list = []
        with open('dld.txt', 'r') as f:
            for i in f:
                num = len(i.split('|'))
                if num == 3:
                    url = i.split('|')[1]
                    name = i.split('|')[2]
                    d = Downloader(self.save_path, url, name, 'mp4')
                    project_list.append(d)
                elif num == 2:
                    url = i.split('|')[0]
                    name = i.split('|')[1]
                    d = Downloader(self.save_path, url, name, 'mp4')
                    project_list.append(d)
        return project_list

    def run(self, download_prject):
        download_prject.run()

    def start(self, max_thread=10):
        t_pool = ThreadPool(max_thread, info=self.info)
        t_pool.add_task_list(self.run, self.download_project_list)
        t_pool.run()
