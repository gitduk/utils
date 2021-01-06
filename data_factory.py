def replaces(*rep_map_list, target=None, replace_key=False):
    """ replace target use rep_map_list

    rep_map_list: replace rules to replace target
    target: to be replace use rep_map_list
    replace_key: if set to True and type of target is dict, target keys will be repalce by rules
    """
    for rep_map in rep_map_list:
        if not isinstance(rep_map, dict):
            values = ['' for _ in rep_map]
            rep_map = dict(zip(list(rep_map), values))
        for k, v in rep_map.items():

            # process target type
            if type(target).__name__ == 'str' and target != '':
                target = target.replace(k, v)
            elif type(target).__name__ == 'list':
                rep_str = '|'.join(target)
                target = rep_str.replace(k, v).split('|')

            # target is a dict
            elif type(target).__name__ == 'dict':
                new_target = {}
                for k_, v_ in target.items():
                    v_ = v_ if v_ else ''
                    if not replace_key:
                        target[k_] = v_.replace(k, v)
                    else:
                        new_key = k_.replace(k, v)
                        new_value = v_.replace(k, v)
                        new_target[new_key] = new_value
                target = new_target

            elif target is None:
                raise Exception('target is None')

    return target


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
