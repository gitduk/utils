import os
import sys
import time
from tools.timer import Time
import requests
from tools.logger import Logger
from tools.multithread import ThreadPool
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

lg = Logger()


class Downloader(object):
    def __init__(self, path, url, name, postfix='mp4'):
        self._path = path
        self._url = url
        self._name = name
        self._max_retry = 3
        self.postfix = postfix
        self.time = Time()
        self.time.set_fmt('%H:%M:%S')
        if not os.path.exists(path):
            os.makedirs(path)

    def __repr__(self):
        return '{}|{}|{}'.format(self._name, self.postfix, self._url)

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

    def run(self):
        max_retry_count = self.max_retry
        retry_count = 0
        while retry_count < max_retry_count:
            try:
                self.start_download()
                break
            except Exception as Ex:
                lg.error()
                retry_count += 1

        if retry_count >= max_retry_count:
            resp = requests.get(self._url)
            if resp.status_code != 404:
                time.sleep(60)
                try:
                    self.start_download()
                except:
                    lg.error()
            lg.warning("Download failed|{}".format(resp.status_code))

    @lg.log()
    def start_download(self):
        # deal with file type
        chunk_size = 1024
        self._name = self._name.strip().strip('.mp4')
        if self.postfix == 'img':
            time.sleep(1)
            chunk_size = 32
            self.postfix = self._url.split('.')[-1]

        # print('\n' + '-' * 100)
        start = time.time()
        _file_path = '{}/[✴]{}.{}'.format(self._path, self._name, self.postfix)
        file_path = '{}/{}.{}'.format(self._path, self._name, self.postfix)

        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            lg.info("File downloaded|{:.2f}MB|{}|{}".format(file_size / (1024 * 1024), self._name, self._url))
            return

        with requests.session() as req:
            req.stream = True
            req.verify = False
            req.timeout = 10
            req.headers = {
                "Accept-Encoding": "identity;q=1, *;q=0",
                "Range": None,
                "Referer": self._url,
                # "Connection": "Close",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.59 Safari/537.36 115Browser/8.6.2"
            }
            # ================================================= first request get total length
            resp = req.get(self._url)
            is_chunked = resp.headers.get('transfer-encoding', '') == 'chunked'
            content_length_s = resp.headers.get('content-length')
            if not is_chunked and content_length_s.isdigit():
                total_length = int(content_length_s)
            else:
                total_length = None
                lg.warning('Content-Lenght is null|{}|{} |{}'.format(self._name, self._url, resp.status_code))
                return

            content_offset = 0
            if os.path.exists(_file_path):
                content_offset = os.path.getsize(_file_path)
                lg.info(
                    'Continue to download|{:.2f}MB/{:.2f}MB|{}|{}'.format(content_offset / (1024 * 1024),
                                                                          total_length / (1024 * 1024), self._name,
                                                                          self._url)
                )
            else:
                lg.info(
                    "Start to download|{:.2f}MB|{}|{}".format(total_length / (1024 * 1024), self._name, self._url))

            # =================================================== second request with head to download the remain data
            req.headers = {'Range': "bytes=%d-%d" % (content_offset, content_offset + total_length)}
            resp = req.get(self._url)
            size = content_offset
            fmt = ''
            pre_module = sys._getframe(1).f_code.co_filename.split('/')[-1].split('.')[0]
            with open(_file_path, 'ab') as file:
                progress_bar_length = 30
                for data in resp.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    size += len(data)
                    done = int(progress_bar_length * size / total_length)
                    lg.info(
                        "[{}{}] [{:.2f}MB] [{:.2f}MB] [{}]".format('=' * done, ' ' * (progress_bar_length - done),
                                                                   size / (1024 * 1024),
                                                                   total_length / (1024 * 1024), self._name,
                                                                   # str(round(float(size / total_length) * 100, 2)), # %
                                                                   ), end='')
                    file.flush()
                os.rename(_file_path, file_path)
            end = time.time()
            lg.info(
                "Download successfully|{:.2f}S|{:.2f}MB|{}|{}".format(end - start, total_length / (1024 * 1024),
                                                                      self._name, self._url))

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
    def __init__(self, file_path, save_path, info=False):
        self.file_path = file_path
        self.save_path = save_path
        self.info = info
        self.selector = {'txt': '|', 'csv': ','}

    @property
    def downloader_list(self):
        project_list = []
        symbol = self.selector[self.file_path.split('.')[-1]]
        with open(self.file_path, 'r') as f:
            lines = f.readlines()
            if symbol == ',':
                lines = lines[1:]
            for i in lines:
                num = len(i.split(symbol))
                if num == 3:
                    url = i.split(symbol)[1]
                    name = i.split(symbol)[2]
                    d = Downloader(self.save_path, url, name, 'mp4')
                    project_list.append(d)
                elif num == 2:
                    url = i.split(symbol)[0]
                    name = i.split(symbol)[1]
                    d = Downloader(self.save_path, url, name, 'mp4')
                    project_list.append(d)
        return project_list

    def run(self, download_prject):
        download_prject.run()

    def start(self, max_thread=10):
        t_pool = ThreadPool(max_thread, info=self.info)
        key = self.file_path.split(".")[-1]
        t_pool.add_task_list(self.run, self.downloader_list)
        t_pool.execute_task()
