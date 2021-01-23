import requests.utils
from data_factory import printer
from web_crawler import ParamFactory

url = 'https://www.baidu.com'
headers = 'User-Agent:Mozilla/5.0 (Linux; U; Android 2.2; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'

ctor = ParamFactory(url, header=headers, cookie='hi=hello')
ctor.update('key', 'hi')
resp = requests.get(ctor.url, headers=ctor.headers)
printer(resp)
ctor.update(resp)
ctor.update('hi', 'hihihi')
print(ctor)
print(ctor.cookie_jar.items())
