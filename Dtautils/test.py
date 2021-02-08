from Dtautils.web_crawler import Spider
from concurrent.futures import ThreadPoolExecutor

url = 'http://www.gxlawyer.org.cn/searchLawyer?gender=&practiceScope=43ea076234e049579dd12b9715c6783f&page=1'

sp = Spider(url=url)

pool = ThreadPoolExecutor(max_workers=100)

l = []
L = set(_ for _ in range(1, 357))


def get(sp):
    l.append(sp.css('a.active::text'))
    print(sorted(list((L - set([int(_) for _ in l])))))
    print(sp.speed)
    print(sp.running_time)
    print(sp.failed_requests)


while not sp.complete:
    sp.update('page', pages='共\d+条记录 \d+/(\d+?)页', prepare=True)
    pool.submit(get, sp)
