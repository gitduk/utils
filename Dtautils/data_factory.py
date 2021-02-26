import re
from collections import defaultdict
from collections.abc import Iterable
from Dtautils.tools import _flatten


def search(key, data=None, target_type=None):
    my_dict = defaultdict(list)
    for k, v in _flatten(data):
        my_dict[k].append(v)

    if isinstance(key, Iterable) and not isinstance(key, (str, bytes)):
        return {
            k: [_ for _ in my_dict.get(k) if isinstance(_, target_type)] if target_type else my_dict.get(k)
            for k in key
        }
    else:
        result = [_ for _ in my_dict.get(key) if isinstance(_, target_type)] if target_type else my_dict.get(key)
        return result[0] if len(result) == 1 else result


def strip(*args, data=None, strip_key=False):
    for rule in args:
        assert isinstance(rule, (str, list, tuple)), f'args must be str、list or tuple, get {rule}'
        if isinstance(rule, str): rule = [rule]

        for r in rule:
            result = {}
            for key, value in data.items():
                key, value = _strip(key, value, r, strip_key=strip_key)
                result[key] = value
            data = result

    return data


def _strip(key, value, rule, strip_key=False):
    key = key.replace(rule, '') if strip_key else key

    if isinstance(value, (str, int, float)):
        value = value if not isinstance(value, str) else value.replace(rule, '')
    elif isinstance(value, dict):
        value = strip(rule, data=value, strip_key=strip_key)
    elif isinstance(value, list):
        value = _process_list(key, value, rule, process_key=strip_key)

    return key, value


def _process_list(key, value, rule, process_key=False):
    s = False
    if isinstance(rule, str): rule, s = (rule, ''), True

    result = []
    for v in value:
        if isinstance(v, str):
            result.append(v.replace(*rule))
        elif isinstance(v, list):
            if s:
                v = _strip(key, v, rule[0], strip_key=process_key)
            else:
                v = replace(replace_key=process_key, data={'_': v}, replace_map={rule[0]: rule[1]})

            result.append(v)
        elif isinstance(v, dict):
            if s:
                v = strip(rule, data=v, strip_key=process_key)
            else:
                v = replace(replace_key=process_key, data=v, replace_map={rule[0]: rule[1]})
            result.append(v)
        else:
            result.append(v)

    return result


def replace(replace_map=None, data=None, replace_key=False):
    assert isinstance(data, dict), 'item must be dict'

    for r_key, r_value in replace_map.items():
        result = {}
        for key, value in data.items():
            key = key if not replace_key else key.replace(r_key, r_value)
            if isinstance(value, str):
                result[key] = value.replace(r_key, r_value)
            elif isinstance(value, dict):
                result[key] = replace(data=value, replace_key=replace_key, replace_map={r_key: r_value})
            elif isinstance(value, list):
                result[key] = _process_list(key, value, rule=(r_key, r_value), process_key=replace_key)
            else:
                result[key] = value
        data = result

    return data


def flatten(data, ign=(str, bytes)):
    for k, v in data.items():
        if isinstance(v, dict) and not isinstance(v, ign):
            yield from _flatten(v)
        else:
            yield k, v


def update(update_map, data=None, update_type=(str, int)):
    assert isinstance(data, dict), 'item must be dict'

    for u_key, u_value in update_map.items():
        result = {}
        for key, value in data.items():
            if isinstance(value, update_type):
                result[key] = u_value if key == u_key else value
            elif isinstance(value, dict):
                result[key] = update(update_map={u_key: u_value}, data=value)
            else:
                result[key] = value
        data = result

    return data


# TODO ...
class Re(object):
    def __init__(self, data, match_mode=None):
        self.data = data
        self.match_mode = match_mode or 0


class DictFactory(object):
    def __init__(self, data):
        assert isinstance(data, dict), 'item must be a dict'
        self.data = data

    def search(self, key, data=None, target_type=None):
        return search(key, data=data or self.data, target_type=target_type)

    def strip(self, *args, data=None, strip_key=False):
        return strip(*args, data=data or self.data, strip_key=strip_key)

    def replace(self, replace_map=None, data=None, replace_key=False):
        return replace(replace_map=replace_map, data=data or self.data, replace_key=replace_key)

    def update(self, update_map=None, data=None):
        return update(update_map, data=data or self.data, update_type=(str, int))
