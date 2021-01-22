import time
from copy import deepcopy

import requests


class Replacer(object):
    """ change or replace data from string, list or dict
    """

    def __init__(self, *rules, data=None, replace_key=False, mode='replace', dtype=None):
        self.rules = rules if data else rules[:-1]
        self._data = deepcopy(data) if data else rules[-1]
        self.replace_key = replace_key
        self.dtype = dtype
        self.search_result = {}
        self.mode = mode
        if self.mode in ['search', 'delete']:
            self._arg_keys = self.arg_keys()
        elif self.mode == 'update':
            self._update_dict = self.update_dict()

    @property
    def data(self):
        self._data = self.process(data=self._data)
        return self._data

    # --------------------------------------------------------------------------------- core function
    def process(self, key=None, data=None):
        """ 遍历整个数据 for search mode and delete mode

        :param data: dict or list
        :return: dict or list
        """
        if self.mode == 'delete':
            for k in self._arg_keys:
                try:
                    del data[k]
                except:
                    continue
        elif self.mode == 'search':
            if key and key in self._arg_keys:
                self.update_search_result(key, data)

        if isinstance(data, dict):
            # process dict data in here

            for k, value in data.items():
                if not isinstance(value, (list, dict)):
                    data[k] = self.apply_rule(key=key, value=value)
                else:
                    data[k] = self.process(k, value)

                # search core
                if self.mode == 'search' and k in self._arg_keys:
                    self.update_search_result(k, value)

        elif isinstance(data, list):
            # process list data in here
            _data = []
            for d in data:

                if not isinstance(d, (list, dict)):
                    _data.append(self.apply_rule(key=key, value=d))
                else:
                    _data.append(self.process(key=key, data=d))

            return _data
        else:
            raise Exception('Data Type Error ... data type is unsupported')

        return data

    def apply_rule(self, key=None, value=None):
        """ 处理数据 process other type data in here
        for replace, update, search mode

        :param key:str, int, float or others
        :param value: all types
        :return:value
        """

        if self.mode == 'replace':
            # replace police
            if isinstance(value, (int, float)):
                return value

            for rule in self.rules:
                if isinstance(rule, (int, float)): continue

                if isinstance(rule, (str, list)):
                    for r in list(rule):
                        if isinstance(r, (int, float)): continue
                        value = value.replace(r, '')
                elif isinstance(rule, dict):
                    for k, v in rule.items():
                        value = value.replace(k, v)

        elif self.mode == 'update':
            if key and key in self._update_dict.keys():
                value = self._update_dict.get(key)

        elif self.mode == 'search' and key and key in self._arg_keys:
            self.update_search_result(key, value)

        return value

    def arg_keys(self):
        keys = []
        for rule in self.rules:
            if isinstance(rule, str):
                keys.append(rule)
            elif isinstance(rule, list):
                keys.extend(rule)
            elif isinstance(rule, dict):
                keys.extend(rule.keys())
        return keys

    def update_search_result(self, key, value):
        if key in self.search_result.keys():
            if not isinstance(self.search_result.get('key'), list):
                self.search_result[key] = [self.search_result.pop(key), value]
            elif not isinstance(value, list):
                self.search_result[key].append(value)
            else:
                self.search_result[key].extend(value)
        else:
            self.search_result[key] = value

    def update_dict(self):
        up_dict = {}
        if len(self.rules) == 1 and isinstance(self.rules[0], dict):
            up_dict = self.rules[0]
        elif len(self.rules) == 2 and isinstance(self.rules[0], str):
            up_dict = dict([self.rules])

        elif len(self.rules) == 2 and isinstance(self.rules[0], list):
            up_dict = dict(list(zip(self.rules)))

        elif len(self.rules) == 2 and isinstance(self.rules[0], dict):
            for k, v in self.rules[0].items():
                value = self.rules[1].get(v)
                up_dict[k] = value

        elif len(self.rules) == 3 and isinstance(self.rules[0], list) and isinstance(self.rules[2], dict):
            for k, v in zip(self.rules[0], self.rules[1]):
                value = self.rules[2].get(v)
                up_dict[k] = value
        else:
            raise Exception('Args Format Error ... unsupported args format')

        return up_dict


class Printer(object):
    def __init__(self, data=None):
        self.data = data if data else ''
        self.data_groups = []
        self.information_extractor()
        self.printer()

    def information_extractor(self):
        if isinstance(self.data, requests.models.Response):
            group_one = DataGroup('request')
            group_one.add_info('url', self.data.url)

            body = self.data.request.body if self.data.request.body else ''
            headers = self.data.request.headers if self.data.request.headers else ''
            cookies = self.data.request._cookies if self.data.request._cookies else ''

            group_one.add_info('body', body)
            group_one.add_data('headers', headers)
            group_one.add_data('cookies', cookies)

            resp_headers = self.data.headers if self.data.headers else ''
            resp_cookies = self.data.cookies if self.data.cookies else ''
            group_two = DataGroup('response')
            group_two.add_data('headers', resp_headers)
            group_two.add_data('cookies', resp_cookies)

            self.data_groups.append(group_one)
            self.data_groups.append(group_two)

            # elif isinstance(self.data, scrapy.http.response.html.HtmlResponse):
            # self.print_queue['request body'] = self.data.request.body
            # self.print_queue['request header'] = self.data.request.headers
            # self.print_queue['request cookie'] = self.data.request.cookies

            # self.print_queue['response header'] = self.data.request.headers
            ...

    def printer(self):
        for dg in self.data_groups:
            lines = self.parse_data_group(dg)
            for line in lines:
                print(line)

    @staticmethod
    def parse_data_group(data_group):
        bar_length = data_group.bar_length
        head = f'{"+" * (bar_length + len(data_group.name))} {data_group.name}'
        info = data_group.info
        data_pool = data_group.data_pool
        lines = [head]

        # add info to lines
        for info_k, info_v in info.items():
            fmt = '{:<%d} | {:<%d}' % tuple(data_group.max_info_length)
            lines.append(fmt.format(info_k, info_v))

        lines.append('')
        # add data to lines
        for key, value in data_pool.items():
            lines.append(f'{"-" * bar_length} {key}')
            for d_key, d_value in value.items():
                fmt = '{:<%d} | {:<%d}' % tuple(data_group.max_data_length)
                lines.append(fmt.format(d_key, d_value))

            lines.append('')
        return lines


class DataGroup(object):
    def __init__(self, name):
        self.name = name.upper()
        self.data_pool = {}
        self.info = {}
        self.max_info_length = [0, 0]
        self.max_data_length = [0, 0]
        self.bar_length = 0

    def add_data(self, title, data):
        if not data: return
        max_key_length = max([len(_) for _ in data.keys()])
        max_value_length = max([len(_) for _ in data.values()])

        self.max_data_length[0] = max_key_length if max_key_length > self.max_data_length[0] else self.max_data_length[
            0]
        self.max_data_length[1] = max_value_length if max_value_length > self.max_data_length[1] else \
            self.max_data_length[1]
        self.update_bar()

        self.data_pool[title] = data

    def add_info(self, title, info):
        self.max_info_length[0] = len(title) if len(title) > self.max_info_length[0] else self.max_info_length[0]
        self.max_info_length[1] = len(info) if len(info) > self.max_info_length[1] else self.max_info_length[1]
        self.info[title] = info
        self.update_bar()

    def update_bar(self):
        info_length = self.max_info_length[0] + self.max_info_length[1]
        data_length = self.max_data_length[0] + self.max_data_length[1]
        self.bar_length = info_length if info_length > data_length else data_length


class DictFactory(object):

    def del_dict_depth(self, data_dict):
        data = {}
        list_data = {}
        for key, value in data_dict.items():
            value = str(value)
            if isinstance(value, dict):
                data = {**data, **self.del_dict_depth(value)}
            elif isinstance(value, list):
                if not value:
                    continue
                if isinstance(value[0], dict):
                    list_data[key] = self.list_to_dict(value)
                else:
                    value = '|'.join(value)
                data = {**data, key: value}
            else:
                data = {**data, key: value}

        return {**data, **list_data}

    @staticmethod
    def list_to_dict(data_list):
        result = {}
        for data in data_list:
            for key, value in data.items():
                if key in [_ for _ in result.keys()]:
                    value_ = result.get(key)
                    result[key] = f'{value_}|{value}'
                else:
                    result = {**result, key: value}

        return result

    @staticmethod
    def find(target, dict_data, find_key=False):
        queue = [dict_data]
        while len(queue) > 0:
            data = queue.pop()
            for key, value in data.items():
                if key == target:
                    return value
                elif value == target and find_key:
                    return key
                elif type(value) == dict:
                    queue.append(value)
        return ''

    @staticmethod
    def print_table(data, title=None, no_print=None):
        if isinstance(data, requests.cookies.RequestsCookieJar):
            for cookie in iter(data):
                # FIXME ...
                pass

        if isinstance(data, dict):
            key_max_length = max([len(_) for _ in data.keys()])
            value_max_length = max([len(_) for _ in data.values()])
            title_index = (key_max_length + value_max_length) // 2
            if not title: title = 'dict to table'

            head = '-' * title_index + title.center(len(title) + 2, ' ') + '-' * title_index
            lines = [head]
            for key, value in data.items():
                formatter = "{:<%d} | {:<}" % key_max_length
                line = formatter.format(key, str(value))
                lines.append(line)

            # tail = '-' * title_index + '-' * len(title) + '-' * title_index + '--'
            # lines.append(tail)
            if no_print:
                return [_ + '\n' for _ in lines]
            else:
                for line in lines:
                    print(line)


def replacer(*rules, data=None, replace_key=False, mode='replace', dtype=None, count=False):
    result = Replacer(*rules, data=data, replace_key=replace_key, mode=mode, dtype=dtype)
    return result.data if mode != 'search' else result.search_result


def printer(data):
    return Printer(data)


data_ = {
    "ret": 0,
    "content": {
        "pageNum": 1,
        "pageSize": 10,
        "size": 10,
        "startRow": 1,
        "endRow": 10,
        "total": 558,
        "pages": 56,
        "test": ['true', 'false', 'true', 'false'],
        "list": [
            {
                "pageNum": 1,
                "pageSize": 10,
                "sjhm": "0793-5827746",
                "zgzlbmc": "null",
                "total": 225,
                "swsmc": "江西童少华律师事务所",
                "id": 614,
                "nameOfPath": "江西省上饶市弋阳县城南辉煌路3号"
            },
            {
                "pageNum": 1,
                "pageSize": 10,
                "sjhm": "13807931789",
                "total": 225,
                "swsmc": "江西茶乡律师事务所",
                "deptId": "null",
                "id": 615,
                "nameOfPath": "江西省上饶市婺源县文公南路2号光华宾馆"
            }
        ],
        "prePage": 0,
        "nextPage": 2,
        "isFirstPage": "true",
        "isLastPage": "false",
        "hasPreviousPage": "false",
        "hasNextPage": "true",
        "navigatePages": 8,
        "navigatepageNums": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8
        ],
        "navigateFirstPage": 1,
        "navigateLastPage": 8,
        "firstPage": 1,
        "lastPage": 8,
    },
    "total": 23,
    "msg": "操作成功"
}

data = {
    'name': 'kaige',
    'age': '13',
    'address': 'tyds bdong 603'

}

s = time.time()
r = Replacer('lastPage', 'test', data_, mode='search')
print(r.data)
print(r.search_result)
e = time.time()
print(e - s)
