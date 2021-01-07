import re

import requests


class Replacer(object):
    def __init__(self, *rules, data=None, replace_key=False):
        self.rules = rules if data else rules[:-1]
        self.data = data if data else rules[-1]
        self.current_rule = None
        self.replace_key = replace_key
        self.init_rules()
        self.start()

    def start(self):
        for rule in self.rules:
            self.current_rule = rule

            if isinstance(self.data, str):
                self.data = self.str_data_replacer()
            elif isinstance(self.data, (list, dict)):
                self.data = self.dict_data_replacer()

    def init_rules(self):
        new_rules = []
        for rule in self.rules:
            if not isinstance(rule, dict):
                values = ['' for _ in rule]
                rule = dict(zip(list(rule), values))
            new_rules.append(rule)
        self.rules = new_rules

    def str_data_replacer(self, data=None):
        if not data: data = self.data
        for r_key, r_value in self.current_rule.items():
            data = data.replace(r_key, r_value)
        return data

    def dict_data_replacer(self, data=None):
        if not data: data = self.data

        data_type = 'dict'
        if isinstance(data, list): data_type, data = 'list', dict(zip(data, data))

        for r_key, r_value in self.current_rule.items():
            new_data = {}
            for key, value in data.items():
                if self.replace_key and not isinstance(r_value, (int, float)): key = key.replace(r_key, r_value)

                if isinstance(value, str) and not isinstance(r_value, (int, float)):
                    new_data[key] = value.replace(r_key, r_value)
                elif isinstance(value, (list, dict)):
                    new_data[key] = self.dict_data_replacer(value)
                elif isinstance(value, (int, float)) and isinstance(r_value, (int, float)):
                    new_data[key] = r_value
                elif isinstance(value, (int, float)):
                    new_data[key] = value

            data = new_data
        return data if data_type == 'dict' else list(data.values())

    def __repr__(self):
        return repr(self.data)


def del_dict_depth(data_dict):
    data = {}
    list_data = {}
    for key, value in data_dict.items():
        value = str(value)
        if isinstance(value, dict):
            data = {**data, **del_dict_depth(value)}
        elif isinstance(value, list):
            if not value:
                continue
            if isinstance(value[0], dict):
                list_data[key] = trans_list_to_dict(value)
            else:
                value = '|'.join(value)
            data = {**data, key: value}
        else:
            data = {**data, key: value}

    return {**data, **list_data}


def trans_list_to_dict(data_list):
    result = {}
    for data in data_list:
        for key, value in data.items():
            if key in [_ for _ in result.keys()]:
                value_ = result.get(key)
                result[key] = f'{value_}|{value}'
            else:
                result = {**result, key: value}

    return result


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

        tail = '-' * title_index + '-' * len(title) + '-' * title_index
        lines.append(tail)
        if no_print:
            return [_ + '\n' for _ in lines]
        else:
            for line in lines:
                print(line)
