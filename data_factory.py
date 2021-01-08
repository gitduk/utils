import requests
import scrapy


class Replacer(object):
    """ change or replace data from string, list or dict
    """

    def __init__(self, *rules, data=None, replace_key=False, update=False):
        self.rules = rules if data else rules[:-1]
        self.data = data if data else rules[-1]
        self.current_rule = None
        self.replace_key = replace_key
        self.update = update
        self.start()

    def start(self):
        for rule in self.rules:
            if not isinstance(rule, dict):
                values = ['' for _ in rule]
                rule = dict(zip(list(rule), values))
            self.current_rule = rule
            self.data = self.data_replacer()

    def data_replacer(self, data=None):
        if not data: data = self.data
        data_type = type(data).__name__

        if isinstance(data, (list, str)):  data = dict(zip(list(data), list(data)))

        for r_key, r_value in self.current_rule.items():
            new_data = {}
            for key, value in data.items():
                if self.replace_key and not isinstance(r_value, (int, float)): key = key.replace(r_key, r_value)

                # update logical
                if self.update and key != r_key: r_value = value
                if isinstance(value, str) and not isinstance(r_value, (int, float)):
                    new_data[key] = value.replace(r_key, r_value) if not self.update else r_value
                elif isinstance(value, (list, dict)):
                    new_data[key] = self.data_replacer(value)
                elif isinstance(value, (int, float)):
                    new_data[key] = value

            data = new_data

        if data_type == 'dict':
            return data
        elif data_type == 'list':
            return list(data.values())
        elif data_type == 'str':
            return ''.join(list(data.values()))
        else:
            raise Exception('Error data type ...')

    def __repr__(self):
        return repr(self.data)


class Searcher(object):
    ...


class Printer(object):
    def __init__(self, data):
        self.data = data
        self.print_queue = []
        self.information_extractor()
        self.printer()
        self.data_group = []

    def information_extractor(self):
        if isinstance(self.data, requests.models.Response):
            group_one = DataGroup('REQUEST')
            group_one.add_info('url', self.data.url)
            group_one.add_info('body', self.data.request.body)
            group_one.add_data('cookies', self.data.request._cookies)
            group_one.add_data('headers', self.data.request.headers)

            group_two = DataGroup('RESPONSE')
            group_two.add_data('cookies', self.data.cookies)
            group_two.add_data('headers', self.data.headers)

            self.print_queue.append(group_one)
            self.print_queue.append(group_two)

        elif isinstance(self.data, scrapy.http.response.html.HtmlResponse):
            # self.print_queue['request body'] = self.data.request.body
            # self.print_queue['request header'] = self.data.request.headers
            # self.print_queue['request cookie'] = self.data.request.cookies

            # self.print_queue['response header'] = self.data.request.headers
            ...

    def printer(self):
        for dg in self.print_queue:
            half_bar_length = dg.half_bar_length
            name = dg.name
            if not name: name = 'dict to table'

            # print('-' * half_bar_length + str(name.center(len(name) + 2, ' '))) + '-' * half_bar_length
            print('-' * half_bar_length + '-' * half_bar_length)
            for key, value in dg.base_info.items():
                print(f'{key}: {value}')
            for d_name, d_value in dg.data_pool.items():
                for d_k, d_v in d_value:
                    print(f'{d_k}: {d_v}')

            print('-' * (dg.bar_length + len(name) + 2))

    def formatter(self, data, title=None):
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

            tail = '-' * title_index + '-' * len(title) + '-' * title_index + '--'
            lines.append(tail)
            return lines


class DataGroup(object):
    def __init__(self, name):
        self.name = name
        self.data_pool = {}
        self.base_info = {}
        self.info_line_num = 0
        self.data_num = 0
        self.bar_length = 0
        self.half_bar_length = 0

    def add_data(self, title, data):
        if not data: return
        max_key_length = max([len(_) for _ in data.keys()])
        max_value_length = max([len(_) for _ in data.values()])
        self.bar_length += (max_key_length + max_value_length)
        self.half_bar_length = self.bar_length // 2
        self.data_pool[title] = {
            'data': data,
            'lines': len(data.keys()),
            'mex_key_length': max_key_length,
            'mex_value_length': max_value_length,
        }

        # parse information
        self.data_num = len(self.data_pool.keys())

    def add_info(self, title, info):
        self.base_info[title] = info

        # parse information
        self.info_line_num = len(self.base_info.keys())


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
