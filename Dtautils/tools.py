import heapq
import time
from collections import defaultdict
from functools import wraps
import json as Json


class PriorityQueue:
    def __init__(self):
        self._queue = []
        self.index = 0

    def push(self, item, priority):
        heapq.heappush(self._queue, (priority, self.index, item))
        self.index += 1

    def pop(self):
        return heapq.heappop(self._queue)[-1]

    def empty(self):
        return True if not self._queue else False

    def qsize(self):
        return len(self._queue)


def fn_timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print("Function [{}] Spend {:.3f} s".format(func.__name__, end - start))
        return result

    return wrapper


def _flatten(item):
    for k, v in item.items():
        if isinstance(v, dict):
            yield from _flatten(v)
        yield k, v


def json_to_dict(json):
    if isinstance(json, dict): return json

    if not json: json = {}
    json = json.replace('\'', '"')
    try:
        return Json.loads(json)
    except:
        print(f'Invalid json data: {json}')
        return {}


def body_to_dict(data):
    if isinstance(data, dict): return data

    if not data: return {}
    assert '=' in data, f'Invalid data: {data}'
    return dict(_.split('=', 1) for _ in data.split('&'))


def _spilt_url(url):
    if not url: return {}
    path = url.split('?', 1)
    return [path[0], ''] if len(path) == 1 else path


def url_to_dict(url):
    if not url: return {}

    url = url.replace('://', '/')

    _path, _param = _spilt_url(url)
    protocol, domain, *path = _path.split('/')
    if _param:
        if '=' in _param:
            param = dict(p.split('=', 1) for p in _param.split('&'))
        else:
            param = {_param: _param}
    else:
        param = {}

    return {
        'protocol': protocol,
        'domain': domain,
        'path': path,
        'param': param
    }


def headers_to_dict(headers):
    if isinstance(headers, dict): return headers

    if not headers: return {}
    return {_.split(':')[0].strip(): _.split(':')[1].strip() for _ in headers.split('\n')}


def cookies_to_dict(cookies):
    if isinstance(cookies, dict): return cookies

    if not cookies: return {}
    return {_.split('=')[0].strip(): _.split('=')[1].strip() for _ in cookies.split(';')}


def dict_to_body(data: dict):
    return '&'.join([f'{key}={value}' for key, value in data.items()])


def dict_to_json(json: dict):
    return Json.dumps(json)
