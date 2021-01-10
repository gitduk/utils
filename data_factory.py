import requests


# import scrapy

class Replacer(object):
    """ change or replace data from string, list or dict
    """

    def __init__(self, *rules, data=None, replace_key=False, mode='replace', mode_dtype='str'):
        self.rules = rules if data else rules[:-1]
        self._data = data if data else rules[-1]
        self.current_rule = None
        self.replace_key = replace_key
        self.mode = mode
        self.mode_dtype = mode_dtype
        self._search_result = {'str': [], 'list': [], 'dict': [], 'int': [], 'float': []}
        self.police()
        self.start()

    @property
    def data(self):
        return self._data

    @property
    def search_result(self):
        if len(self._search_result.values()) == 1:
            # TODO ...
            return ...
        return self._search_result

    def police(self):
        if self.mode not in ['replace', 'update', 'search', 'delete']:
            raise Exception(f'Mode Name Error ... valid mode: {self.mode}')

        dtype = type(self._data).__name__
        if dtype not in ['str', 'list', 'dict']:
            raise Exception(f'Data Type Error ... valid data type: {dtype}')

    def start(self):
        for rule in self.rules:
            if not isinstance(rule, dict) and self.mode == 'replace':
                values = ['' for _ in rule]
                rule = dict(zip(list(rule), values))

            if not isinstance(rule, dict) and self.mode in ['search', 'delete']:
                if isinstance(rule, str):
                    rule = {rule: rule}
                if isinstance(rule, list):
                    rule = zip(rule, rule)

            self.current_rule = rule
            self._data = self.data_replacer()

    # --------------------------------------------------------------------------------- core function
    def data_replacer(self, data=None):
        if not data: data = self._data
        dtype = type(data).__name__

        if isinstance(data, (list, str)):  data = dict(zip(list(data), list(data)))

        for r_key, r_value in self.current_rule.items():
            new_data = {}
            for key, value in data.items():
                if self.replace_key and not isinstance(r_value, (int, float)):
                    key = key.replace(r_key, r_value)

                if self.mode == 'replace':
                    if isinstance(value, str):
                        new_data[key] = value.replace(r_key, r_value)
                    elif isinstance(value, (int, float)) and isinstance(r_value, (int, float)):
                        new_data[key] = r_value
                    elif isinstance(value, (list, dict)):
                        new_data[key] = self.data_replacer(value)
                    else:
                        new_data[key] = value

                elif self.mode == 'search':
                    if key == r_key:
                        self._search_result.get(type(value).__name__).append(value)
                    if isinstance(value, dict):
                        self.data_replacer(value)

                elif self.mode == 'update':
                    if key == r_key:
                        new_data[key] = r_value
                    elif isinstance(value, (list, dict)):
                        new_data[key] = self.data_replacer(value)
                    else:
                        new_data[key] = value

                elif self.mode == 'delete':
                    if key == r_key and type(value).__name__ == self.mode_dtype:
                        continue
                    else:
                        new_data[key] = value

            data = new_data if self.mode != 'search' else data

        return self.dtype_translater(data, dtype)

    @staticmethod
    def dtype_translater(data, dtype):

        if dtype == 'list':
            data = list(data.values())
        elif dtype == 'str':
            data = ''.join(list(data.values()))

        return data

    def __repr__(self):
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
        head = f'{"=" * (bar_length + len(data_group.name))} {data_group.name}'
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


def replacer(*rules, data=None, replace_key=False, mode='replace', mode_dtype='str'):
    result = Replacer(*rules, data=data, replace_key=replace_key, mode=mode, mode_dtype=mode_dtype)
    return result.data if mode!='search' else result.search_result


def printer(data):
    return Printer(data)


data = {
    'name': 'kaige',
    'age': 25,
    'ls': [1, 2, 3, 4, 5, 6],
    'jn': {
        'sql': ['1', '2', '3'],
        'linux': ['6', '7', '8'],
        'python': [9, 10, 11],
        'others': {
            'no': 0
        }
    }
}

print(replacer('linux', data=data, mode='search'))
