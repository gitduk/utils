def _spilt_url(url=None):
    path = url.split('?', 1)
    return [path[0], ''] if len(path) == 1 else path


def _url_to_dict(url=None):
    url = url.replace('://', '/')

    _path, _param = _spilt_url(url)
    protocol, domain, *path = _path.split('/')
    if _param:
        if '=' in _param:
            param = dict(p.split('=', 1) for p in _param.split('&'))
        else:
            param = {_param: _param}
    else:
        param = {}

    return {
        'protocol': protocol,
        'domain': domain,
        'path': path,
        'param': param
    }


print(_url_to_dict('http://218.94.1.186:8090/lawyerIntegrity/#/lawoffice/lawofficeDetail?hi'))


def _data_to_dict(data):
    if not data: return {}
    assert '=' in data, f'Invalid data: {data}'
    return dict(_.split('=', 1) for _ in data.split('&'))


print(_data_to_dict('h=&H=&hh=hh'))

import json as js


def _json_to_dict(json):
    if not json: json = {}
    json = json.replace('\'', '"')
    try:
        return js.loads(json)
    except:
        print(f'Invalid json data: {json}')
        return {}


j = '{"hi":"hi"}'
print(_json_to_dict(j))
