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
    if not data: args, data = args[:-1], args[-1]

    for st_key in args:
        assert isinstance(st_key, (str, list, tuple)), f'args must be str、list or tuple, get {st_key}'
        if isinstance(st_key, str): st_key = [st_key]

        for r in st_key:
            result = {}
            for key, value in data.items():
                key, value = _strip(key, value, r, strip_key=strip_key)
                result[key] = value
            data = result

    return data


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


def update(update_map, data=None, target_type=None):
    assert isinstance(data, dict), 'item must be dict'
    if not target_type: target_type = (str, bytes, int, float, list, dict)

    for u_key, u_value in update_map.items():
        result = {}
        for key, value in data.items():
            if isinstance(value, target_type):
                result[key] = u_value if key == u_key else value
            elif isinstance(value, dict):
                result[key] = update(update_map={u_key: u_value}, data=value)
            else:
                result[key] = value
        data = result

    return data


def delete(*args, data=None, target_type=None):
    if not data: args, data = args[:-1], args[-1]
    if not target_type: target_type = (str, bytes, int, float, list, dict)

    for d_key in args:
        assert isinstance(d_key, (str, list, tuple)), f'args must be str、list or tuple, get {d_key}'

        if isinstance(d_key, str): d_key = [d_key]
        for d_k in d_key:
            result = {}
            for key, value in data.items():
                if isinstance(value, target_type):
                    if key == d_k:
                        continue
                    else:
                        result[key] = value
                elif isinstance(value, dict):
                    result[key] = delete(d_k, data=value, target_type=target_type)
                else:
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


def flatten(data, ign=(str, bytes)):
    for k, v in data.items():
        if isinstance(v, dict) and not isinstance(v, ign):
            yield from _flatten(v)
        else:
            yield k, v


def re_search(re_map, data, flags=None, index=None):
    assert isinstance(re_map, dict), 'map must be a dict'
    result = {key: re.search(pattern, data, flags=flags or 0) if isinstance(pattern, str) else pattern.search(data)
              for key, pattern in re_map.items()}

    return {key: value.group(index or 0) for key, value in result.items()}


def re_findall(re_map, data, flags=None):
    assert isinstance(re_map, dict), 'map must be a dict'
    return {key: re.findall(pattern, data, flags=flags or 0) if isinstance(pattern, str) else pattern.findall(data)
            for key, pattern in re_map.items()}


def merge(*args, overwrite=False):
    default_dict = defaultdict(list)

    for d in args:
        assert isinstance(d, dict), 'arg must be a dict'
        for k, v in d.items():
            if overwrite and default_dict.get(k) and v in default_dict.get(k): continue
            default_dict[k].append(v)

    return dict(default_dict)


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

    def update(self, update_map=None, data=None, target_type=None):
        return update(update_map, data=data or self.data, target_type=target_type)

    def delete(self, *args, data=None, target_type=None):
        return delete(*args, data=data, target_type=target_type)
