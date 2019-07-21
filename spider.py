# coding = utf-8
#此代码爬取的是漫画堆的移动端

from lxml import etree
import requests
from requests.adapters import HTTPAdapter
import json
from selenium import webdriver

service_args = []
service_args.append('--load-images=false')  ##关闭图片加载
service_args.append('--ignore-ssl-errors=true')  ##忽略https错误
service_args.append('--disk-cache=true')  ##开启缓存

class Spider:
    def __init__(self):
        #计数，达到一定量重启phantomjs
        self.count = 0
        self.browser = webdriver.PhantomJS(service_args=service_args)
        #设置加载页面超时
        self.browser.set_page_load_timeout(5)
        self.s = requests.Session()
        self.s.headers.update({'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'})
        #设置requests的重试次数
        self.s.mount('http://', HTTPAdapter(max_retries=5))
        self.s.mount('https://', HTTPAdapter(max_retries=5))

    #爬取搜索结果
    #kw:关键词
    #p：页数，每页显示20个结果
    def comic_search(self, kw, p):
        URL = 'https://450.manhuadang.net/comic/search'
        if kw is not None:
            URL += '?keywords=' + kw
            if p is not None:
                URL += '&page=' + p
        elif p is not None:
            URL += '?page=' + p
        #timeout()设置超时
        r = self.s.get(URL, timeout=(3, 4))
        data = json.loads(r.text)
        r.close()
        #返回完整结果
        return data

    #爬取漫画详情页
    #name: 漫画名的字母代替，具体参照实际页面
    def comic_item(self, name):
        URL = 'https://m.manhuadui.com/manhua/'
        r = self.s.get(URL + name + "/", timeout=(3, 4))
        h = etree.HTML(r.text)
        #漫画名
        title = "//div[@class='subHeader']/h1[@id='comicName']/text()"
        #封面url
        cover = "//div[@id='Cover']/img/@src"
        #作者
        author = "//div[@class='sub_r autoHeight']/p[1]/text()"
        #类型
        type = "//div[@class='sub_r autoHeight']/p[2]/a/text()"
        #分类
        category = "//div[@class='sub_r autoHeight']/p[3]/a[1]/text()"
        #地区
        area = "//div[@class='sub_r autoHeight']/p[3]/a[2]/text()"
        #状态
        status = "//div[@class='sub_r autoHeight']/p[3]/a[3]/text()"
        #更新日期
        update = "//div[@class='sub_r autoHeight']/p[5]/span[2]/text()"
        #章节名
        chapterName = "//div[@class='chapter-warp']/ul/li/a/span[1]/text()"
        #各章节地址
        chapterURL = "//div[@class='chapter-warp']/ul/li/a/@href"
        r.close()
        return {
            "title": h.xpath(title),
            "cover": h.xpath(cover),
            "author": h.xpath(author),
            "category": h.xpath(category),
            "type": h.xpath(type),
            "area": h.xpath(area),
            "status": h.xpath(status),
            "update": h.xpath(update),
            "chapterName": h.xpath(chapterName)[::-1],
            "chapterURL": h.xpath(chapterURL)[::-1]
        }
    #爬取漫画章节具体内容
    #URL: 该章节具体地址，为移动端地址
    #p: 页数
    def comic_img(self, URL, p):
        #爬取一次，计数
        self.count = self.count + 1
        if p is not None:
            URL += '?p=' + p
        i = 0
        while i < 6:
            try:
                self.browser.get(URL)
                h = etree.HTML(self.browser.page_source)
                # 当前章节名
                this = "//div[@class='subHeader']/a[@class='BarTit']/text()"
                # 当前章节名
                thisChapter = h.xpath(this)[0].replace('\n', '').strip()
                i = 6
            except(Exception):
                print(Exception)
                i += 1
        #获取前一章的内容
        prev = self.browser.execute_script('return prevChapterData')
        # 获取下一章的内容
        next = self.browser.execute_script('return nextChapterData')
        #漫画名的字母代替
        slug = "//a[@class='iconRet']/@href"
        #漫画名+漫画章节名
        title = "//head/meta[@name='keywords']/@content"
        #当前具体漫画图片的地址
        img = "//div[@id='images']/img/@src"
        #当前页数和总页数
        page = "//div[@id='images']/p/text()"
        #漫画名
        titleName = h.xpath(title)[0].replace(thisChapter, '')
        #因爬取后phantomjs的内存占用越来越多，所以采用这样的笨方法
        #另一点，这里我认为应该新开一个线程来重启，我这样会使等待延长很多，但是我不太会
        #当计数到20之后，重启phantomjs
        # self.browser.delete_all_cookies()
        if(self.count > 20):
            self.browser.quit()
            self.browser = webdriver.PhantomJS(service_args=service_args)
            self.browser.set_page_load_timeout(5)
            self.count = 0
        return {
            'prev': prev,
            'next': next,
            "title": titleName,
            "this": thisChapter,
            "img": h.xpath(img),
            "page": h.xpath(page),
            "slug": h.xpath(slug)[0].replace('https://m.manhuadui.com/manhua/', '')[:-1]
        }

if __name__ == '__main__':
    kw = '进'
    name = 'haizeiwang'
    comic = "https://m.manhuadui.com/manhua/haizeiwang/296660.html"

    sp = Spider()
    search = sp.comic_search(kw, '1')
    print('search', search)
    item = sp.comic_item(name)
    print('item', item)
    img = sp.comic_img(comic, '1')
    print('img', img)