import time
from Dtautils.web_crawler import Spider

url = 'https://blog.csdn.net/qq_24047235/article/details/110215285?q=1'
sp = Spider(url)

start = time.time()
for i in range(1000000):
    sp.update('q', str(i))

end = time.time()
print(end - start)
