import re
from copy import deepcopy
import time
import requests


class DataIter(object):
    """ change or replace data from string, list or dict
    """

    def __init__(self, *rules, data=None, replace_key=False, mode='replace', **kwargs):
        self._rules = rules if data else rules[:-1]
        self._data = deepcopy(data) if data else rules[-1]

        self.replace_key = replace_key
        self.mode = mode
        self.kwargs = kwargs

        assert mode in ['replace', 'update', 'search', 'delete'], f'Invalid mode ... {mode}'

        if self.mode in ['search', 'delete']:
            self._rule_keys = self.get_rule_keys()
        elif self.mode == 'update':
            self._update_dict = self.rules_to_dict()

        self._result = {}

    @property
    def result(self):
        if self.mode in ['replace', 'update', 'delete']: self._result = self.iter_data(self._data)
        if self.mode in ['search']: self.iter_data(self._data)
        if isinstance(self._result, dict):
            return self._result if len(self._result.keys()) != 1 else list(self._result.values())[0]
        else:
            return self._result

    @property
    def rules(self):
        return self._rules

    @rules.setter
    def rules(self, rules):
        self._rules = rules
        self._rule_keys = self.get_rule_keys()
        self._update_dict = self.rules_to_dict()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = deepcopy(data)

    # --------------------------------------------------------------------------------- core function
    def iter_data(self, data=None):
        """ 遍历整个数据 for search mode and delete mode

        :param data: dict or list or str
        :return: dict or list
        """
        if isinstance(data, dict):
            # process dict data here
            _data = {}
            for k, value in data.items():
                if k == value in [None, '', 'None']: continue
                # process key and value in here which value type is list or dict

                # delete key:value which key in rule key list
                if self.mode == 'delete' and k in self._rule_keys: continue

                trans = False
                if isinstance(value, tuple): value, trans = list(value), True
                value = self._bypass(key=k, value=value, passing='dict')
                if trans: value = tuple(value)

                if isinstance(value, tuple):
                    k, value = value if not trans else (k, value)
                elif isinstance(value, list):
                    k, value = k, [_[1] if isinstance(_, tuple) else _ for _ in value]

                if self.mode == 'replace' and self.replace_key and isinstance(value, (tuple, list, dict)):
                    k = self.replacer(value=k)
                _data[k] = value

        elif isinstance(data, list):
            # process list data here
            _data = []
            for dt in data:
                _data.append(self._bypass(value=dt, passing='list'))

        elif isinstance(data, str):
            _data = self._bypass(value=data, passing='str')
        else:
            raise Exception('Data Type Error ... data type is unsupported')

        return _data

    def _bypass(self, key=None, value=None, passing=None):
        # all key will pass here
        if self.mode == 'search' and key in self._rule_keys: self.update_result(key=key, value=value)
        if self.mode == 'update' and key in self._update_dict.keys(): return key, self._update_dict.get(key)

        if isinstance(value, (list, dict)):
            return self.iter_data(value)
        elif passing == 'dict':
            return self._process_dict_value(key=key, value=value)
        elif passing == 'list':
            return self._process_list_value(value)
        else:
            return self._process_text(value)

    def _process_dict_value(self, key, value):
        # process value in dict here, value is not list or dict
        return self.replacer(key=key, value=value) if self.mode == 'replace' else (key, value)

    def _process_list_value(self, value):
        # process value in list here, value is not list or dict
        return self.replacer(value=value) if self.mode == 'replace' else value

    def _process_text(self, data):
        if not data: data = self._data
        match_mode, re_method, group_index = self.kwargs.get('match_mode'), self.kwargs.get(
            're_method'), self.kwargs.get('group_index')

        match_mode_dict = {
            'S': re.S,
            'M': re.M,
            'I': re.I,
            'L': re.L,
            'U': re.U,
            'X': re.X
        }
        method_dict = {
            'search': re.search,
            'match': re.match,
            'findall': re.findall
        }
        match_mode = match_mode_dict.get(match_mode)

        start = time.time()
        for key, re_rule in self.rules_to_dict().items():
            result = method_dict.get(re_method)(re_rule, data, flags=match_mode or 0)

            if re_method == 'search':
                if not group_index:
                    self._result[key] = result.group() if result else ''
                else:
                    self._result[key] = result.group(group_index) if result else ''
            elif re_method == 'match':
                self._result[key] = result.group(group_index) if result else ''
            elif re_method == 'findall':
                self._result[key] = result
            else:
                raise Exception(f'Re Mode Error ... {re_method}')
        end = time.time()
        if end - start > 1:
            print(f'maybe you need to change your re rule {end - start}')
        return data

    def update_result(self, key, value):
        if key in self._result.keys():
            if not isinstance(self._result.get(key), list):
                self._result[key] = [self._result.pop(key), value]
            elif not isinstance(value, list):
                self._result[key].append(value)
            else:
                self._result[key].extend(value)
        else:
            self._result[key] = value

    def replacer(self, key=None, value=None):

        for rule in self.rules:
            if isinstance(rule, (str, list)):
                for rl in rule:
                    if key and self.replace_key: key = key.replace(rl, '') if hasattr(key, 'replace') else key
                    value = value.replace(rl, '') if hasattr(value, 'replace') else value

            elif isinstance(rule, dict):
                for r_key, r_value in rule.items():
                    if key and self.replace_key: key = key.replace(r_key, r_value) if hasattr(key, 'replace') else key
                    value = value.replace(r_key, r_value) if hasattr(value, 'replace') else value
            else:
                print(f'Invalid rule type ... {type(rule)}')

        return (key, value) if key else value

    def get_rule_keys(self):
        keys = []
        for rule in self.rules:
            if isinstance(rule, str):
                keys.append(rule)
            elif isinstance(rule, list):
                keys.extend(rule)
            elif isinstance(rule, dict):
                keys.extend(rule.keys())
        return keys

    def rules_to_dict(self):
        rule_dict = {}
        if self.mode == 'update':
            if len(self.rules) == 1 and isinstance(self.rules[0], dict):
                rule_dict = self.rules[0]

            elif len(self.rules) == 2 and isinstance(self.rules[0], str) and isinstance(self.rules[1], str):
                rule_dict = dict([self.rules])

            elif len(self.rules) == 2 and isinstance(self.rules[0], list) and isinstance(self.rules[1], list):
                rule_dict = dict(list(zip(self.rules)))

            elif len(self.rules) == 2 and isinstance(self.rules[0], list) and isinstance(self.rules[1],
                                                                                         (str, int, float)):
                rule_dict = dict((_, self.rules[1]) for _ in self.rules[0])

            elif len(self.rules) == 2 and isinstance(self.rules[0], dict) and isinstance(self.rules[0], dict):
                for k, v in self.rules[0].items():
                    value = self.rules[1].get(v)
                    rule_dict[k] = value

            # list,list,dict
            elif len(self.rules) == 3 and isinstance(self.rules[0], list) and isinstance(self.rules[2], dict):
                for k, v in zip(self.rules[0], self.rules[1]):
                    value = self.rules[2].get(v)
                    rule_dict[k] = value
            else:
                raise Exception(f'Args Format Error ... unsupported args format : {self.rules}')

        elif self.mode == 'search':
            for rule in self.rules:
                if isinstance(rule, str):
                    rule_dict[rule] = rule
                elif isinstance(rule, list):
                    rule_dict = {**rule_dict, **dict(list(zip(rule, rule)))}
                elif isinstance(rule, dict):
                    rule_dict = {**rule_dict, **rule}
                else:
                    print(f'Rule Type Error ... {type(rule)}')

        else:
            raise Exception(f'Rule To Dict Error ... unsupported mode: {self.mode}')

        return rule_dict


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
