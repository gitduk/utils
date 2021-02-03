from Dtautils.web_crawler import Spider

url = 'https://blog.csdn.net/qq_24047235/article/details/110215285'
sp = Spider(url)
print(sp.xpath('//div[@id="asideProfile"]//text()'))

item_re = {
    'name': '作者',
    'age': 'BitHachi',
}
print(sp.find(item_re))
