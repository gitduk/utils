from Dtautils.web_crawler import Spider

url = 'https://blog.csdn.net/qq_24047235/article/details/110215285'
sp = Spider(url)
print(sp.referer)
print(sp.xpath('//div[@id="asideProfile"]//text()'))
print(sp.headers)

sp.update('details', 'details-me', prepare=True)
print(sp.url)
print(sp.referer)
print(sp.resp.request.headers)
