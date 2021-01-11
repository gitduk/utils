from copy import deepcopy

import requests


class Replacer(object):
    """ change or replace data from string, list or dict
    """

    def __init__(self, *rules, data=None, replace_key=False, mode='replace', mode_dtype=None):
        self.rules = rules
        self._data = deepcopy(data)
        self.current_rule = None
        self.replace_key = replace_key
        self.mode = mode
        self.mode_dtype = mode_dtype
        self._search_result = {'str': [], 'list': [], 'dict': [], 'int': [], 'float': []}
        self.count = [0, 0, 0]
        self.police()
        self.start()

    @property
    def data(self):
        return self._data

    @property
    def search_result(self):
        result = [_ for _ in self._search_result.values() if _]
        if len(result) == 1:
            return result[0][0] if len(result[0]) == 1 else result[0]
        else:
            return self._search_result

    def police(self):
        self.rules = self.rules if self._data else self.rules[:-1]
        self._data = self._data if self._data else self.rules[-1]

        # check rule
        for r in self.rules:
            if self.mode == 'replace':
                if isinstance(r, (int, float)): raise Exception('Rule Type Error ... rule must be str in replace mode')
            elif self.mode == 'update':
                if not isinstance(r, dict): raise Exception('Rule Type Error ... rule must be dict in update mode')

        # check other options
        dtype = type(self._data).__name__
        if dtype not in ['str', 'list', 'dict']:
            raise Exception(f'Data Type Error ... valid data type: {dtype}')

        if self.mode not in ['replace', 'update', 'search', 'delete']:
            raise Exception(f'Mode Name Error ... valid mode: {self.mode}')

        self.mode_dtype = self.mode_dtype if self.mode_dtype else ['str', 'list', 'dict', 'int', 'float']
        if isinstance(self.mode_dtype, str):
            self.mode_dtype = [self.mode_dtype]

    def start(self, rules=None):
        rules = rules if rules else self.rules
        for rule in rules:
            if not isinstance(rule, dict):
                if self.mode == 'replace':
                    values = ['' for _ in rule]
                    rule = dict(zip(list(rule), values))

                else:
                    if isinstance(rule, str):
                        rule = {rule: rule}
                    if isinstance(rule, list):
                        self.start(rule)
                        continue

            self.count[0] += 1
            self.current_rule = rule
            self._data = self.data_replacer()

    # --------------------------------------------------------------------------------- core function
    def data_replacer(self, data=None):
        if not data: data = self._data
        dtype = type(data).__name__

        if isinstance(data, (list, str)):  data = dict(zip(list(data), list(data)))
        for r_key, r_value in self.current_rule.items():
            self.count[1] += 1
            for key, value in data.items():
                self.count[2] += 1

                if type(value).__name__ not in self.mode_dtype:
                    continue

                if self.mode == 'replace':
                    # replace key
                    if self.replace_key and not isinstance(r_value, (int, float)):
                        key, value = key.replace(r_key, r_value), data.pop(key)
                        data[key] = value

                    if isinstance(value, str):
                        data[key] = value.replace(r_key, r_value)
                    elif isinstance(value, (int, float)):
                        data[key] = r_value if isinstance(r_value, (int, float)) else value
                    elif isinstance(value, (list, dict)):
                        data[key] = self.data_replacer(value)
                    else:
                        raise Exception('Value Type Error ... value type is unknown')

                elif self.mode == 'search':
                    if key == r_key:
                        self._search_result.get(type(value).__name__).append(value)
                    elif isinstance(value, dict):
                        self.data_replacer(value)

                elif self.mode == 'update':
                    if key == r_key:
                        data[key] = r_value
                    elif isinstance(value, (list, dict)):
                        data[key] = self.data_replacer(value)

                elif self.mode == 'delete':
                    if key == r_key:
                        del data[key]

        return self.dtype_translater(data, dtype)

    @staticmethod
    def dtype_translater(data, dtype):
        if dtype == 'list':
            return list(data.values())
        elif dtype == 'str':
            return ''.join(list(data.values()))
        else:
            return data

    def __repr__(self):
        print(f'count: {self.count}')
        return repr(self.data) if self.mode != 'search' else repr(self.search_result)


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


def replacer(*rules, data=None, replace_key=False, mode='replace', mode_dtype=None, count=False):
    result = Replacer(*rules, data=data, replace_key=replace_key, mode=mode, mode_dtype=mode_dtype)
    if count:
        print(f'rule count: {result.count}')
    return result.data if mode != 'search' else result.search_result


def printer(data):
    return Printer(data)
