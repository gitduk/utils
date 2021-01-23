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
            # process dict data here

            for k, value in data.items():
                if not isinstance(value, (list, dict)):
                    data[k] = self.apply_rule(key=k, value=value)
                else:
                    if self.mode == 'update' and k in self._update_dict.keys():
                        data[k] = self._update_dict.get(k)
                    else:
                        data[k] = self.process(k, value)

        elif isinstance(data, list):
            # process list data here
            _data = []
            for d in data:

                if not isinstance(d, (list, dict)):
                    _data.append(self.apply_rule(value=d))
                else:
                    _data.append(self.process(data=d))

            return _data
        else:
            raise Exception('Data Type Error ... data type is unsupported')

        return data

    def apply_rule(self, key=None, value=None):
        """ 处理数据 process other type data here
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
            if not isinstance(self.search_result.get(key), list):
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

        elif len(self.rules) == 2 and isinstance(self.rules[0], str) and isinstance(self.rules[2], str):
            up_dict = dict([self.rules])

        elif len(self.rules) == 2 and isinstance(self.rules[0], list) and isinstance(self.rules[1], list):
            up_dict = dict(list(zip(self.rules)))

        elif len(self.rules) == 2 and isinstance(self.rules[0], list) and isinstance(self.rules[1], (str, int, float)):
            up_dict = dict((_, self.rules[1]) for _ in self.rules[0])

        elif len(self.rules) == 2 and isinstance(self.rules[0], dict) and isinstance(self.rules[0], dict):
            for k, v in self.rules[0].items():
                value = self.rules[1].get(v)
                up_dict[k] = value

        # list,list,dict
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

    def printer(self):
        for dg in self.data_groups:
            lines = self.parse_data_group(dg)
            for line in lines:
                print(line)

    def information_extractor(self):
        if isinstance(self.data, requests.models.Response):
            data_dict = {
                'url': self.data.url,
                'body': self.data.request.body,
                'headers': self.data.request.headers,
                'cookies': self.data.request._cookies,
            }
            self.add_to_data_group('request', data_dict)

            data_dict = {
                'headers': self.data.headers,
                'cookies': self.data.cookies,
            }
            self.add_to_data_group('response', data_dict)

    def add_to_data_group(self, name, data_dict):
        group = DataGroup(name)
        for key, value in data_dict.items():
            if not value: value = ''
            if isinstance(value, str):
                group.add_info(key, value)
            else:
                group.add_data(key, value)
        self.data_groups.append(group)

    @staticmethod
    def parse_data_group(data_group):
        bar_length = data_group.bar_length
        head = f'{data_group.name} {"+" * (bar_length + len(data_group.name))}'
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
            lines.append(f'{key} {"-" * bar_length}')
            for d_key, d_value in value.items():
                fmt = '{:<%d} | {:<%d}' % tuple(data_group.max_data_length)
                lines.append(fmt.format(str(d_key), str(d_value)))

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
        max_key_length = max([len(str(_)) for _ in data.keys()])
        max_value_length = max([len(str(_)) for _ in data.values()])

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
