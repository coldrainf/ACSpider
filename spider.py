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
        self.browser.set_page_load_timeout(3)
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
        if p is not None:
            URL += '?p=' + p
        i = 0
        while i < 6:
            try:
                # 爬取一次，计数
                self.count = self.count + 1
                self.browser.get(URL)
                h = etree.HTML(self.browser.page_source)
                # 当前章节名
                this = "//div[@class='subHeader']/a[@class='BarTit']/text()"
                # 当前章节名
                thisChapter = h.xpath(this)[0].replace('\n', '').strip()
                i = 6
            except Exception:
                i += 1
        #获取前一章的内容
        prev = self.browser.execute_script('return prevChapterData')
        # 获取下一章的内容
        next = self.browser.execute_script('return nextChapterData')
        cover = self.browser.execute_script('return pageImage')
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
            self.count = 0
            self.browser = webdriver.PhantomJS(service_args=service_args)
            self.browser.set_page_load_timeout(3)
        return {
            'prev': prev,
            'next': next,
            'cover': cover,
            "title": titleName,
            "this": thisChapter,
            "img": h.xpath(img),
            "page": h.xpath(page),
            "slug": h.xpath(slug)[0].replace('https://m.manhuadui.com/manhua/', '')[:-1]
        }

    # 动画时间表
    def animate_table(self):
        URL = 'http://m.yhdm.tv'
        r = self.s.get(URL, timeout=(3, 4))
        h = etree.HTML(r.text.encode('ISO-8859-1'))
        titles = []
        urls = []
        news = []
        newUrls = []
        for index in range(7):
            title = "//div[@class='tlist']/ul[%d]/li/a/text()"
            url = "//div[@class='tlist']/ul[%d]/li/a/@href"
            new = "//div[@class='tlist']/ul[%d]/li/span/a/text()"
            newUrl = "//div[@class='tlist']/ul[%d]/li/span/a/@href"
            titles.append(h.xpath(title%(index+1)))
            urls.append(h.xpath(url%(index+1)))
            news.append(h.xpath(new%(index+1)))
            newUrls.append(h.xpath(newUrl%(index+1)))
        r.close()
        return {
            "title": titles,
            "url": urls,
            "new": news,
            "newUrl": newUrls
        }

    # 动画搜索
    def animate_search(self, kw):
        URL = 'http://m.yhdm.tv/search/'
        if kw is not None:
            URL += kw
        r = self.s.get(URL, timeout=(3, 4))
        h = etree.HTML(r.text)
        # 动画名
        title = "//a[@class='itemtext']/text()"
        # 封面url
        cover = "//div[@class='imgblock']/@style"
        # 最新集
        new = "//div[@class='itemimgtext']/text()"
        # 地址
        url = "//a[@class='itemtext']/@href"
        r.close()
        return {
            "title": h.xpath(title),
            "cover": h.xpath(cover),
            "new": h.xpath(new),
            "url": h.xpath(url)
        }

    # 动画详情页
    def animate_item(self, url):
        URL = 'http://m.yhdm.tv'
        if url is not None:
            URL += url
        r = self.s.get(URL, timeout=(3, 4))
        h = etree.HTML(r.text.encode('ISO-8859-1'))
        # 动画名
        title = "//div[@class='show']/h1/text()"
        # 封面url
        cover = "//div[@class='show']/img/@src"
        # 最新集
        new = "//div[@class='show']/p[2]/text()"
        # 上映日期
        time = "//div[@class='show']/p[3]/text()"
        # 类型
        type = "//div[@class='show']/p[4]/a/text()"
        # 介绍
        info = "//div[@class='info']/text()"
        # 各章节名
        chapterName = "//div[@id='playlists']/ul/li/a/text()"
        # 各章节url
        chapterURL = "//div[@id='playlists']/ul/li/a/@href"
        r.close()
        return {
            "title": h.xpath(title),
            "cover": h.xpath(cover),
            "new": h.xpath(new),
            "time": h.xpath(time),
            "type": h.xpath(type),
            "info": h.xpath(info),
            "chapterName": h.xpath(chapterName),
            "chapterURL": h.xpath(chapterURL)
        }

    #动画页面
    def animate_video(self, url):
        URL = 'http://www.yhdm.tv'
        if url is not None:
            URL += url
        r = self.s.get(URL, timeout=(3, 4))
        h = etree.HTML(r.text.encode('ISO-8859-1'))
        # 动画名
        title = "//div[@class='gohome l']/h1/a/text()"
        url =  "//div[@class='gohome l']/h1/a/@href"
        thisName = "//div[@class='gohome l']/h1/span/text()"
        pn = "//div[@class='fav r']/span/text()"
        pnName = "//div[@class='fav r']/a/text()"
        pnURL = "//div[@class='fav r']/a/@href"
        # 播放器容器，需配合该网站js文件
        player = "//div[@id='playbox']/@data-vid"
        # 各章节名
        chapterName = "//div[@class='movurls']/ul/li/a/text()"
        # 各章节url
        chapterURL = "//div[@class='movurls']/ul/li/a/@href"
        # 当前观看
        this = "//div[@class='movurls']/ul/li[@class='sel']/a/@href"
        r.close()
        return {
            "title": h.xpath(title),
            "url": h.xpath(url),
            "thisName": h.xpath(thisName),
            "pn": h.xpath(pn),
            "pnName": h.xpath(pnName),
            "pnURL": h.xpath(pnURL),
            # "player": etree.tostring(h.xpath(player)[0], encoding='utf-8').decode().replace('/>', '>'),
            "player": h.xpath(player)[0],
            "chapterName": h.xpath(chapterName),
            "chapterURL": h.xpath(chapterURL),
            "this": h.xpath(this)
        }
    #可直接获取video地址，现已作废
    def video(self, URL):
        i = 0
        while i < 6:
            try:
                self.count = self.count + 1
                self.browser.get(URL)
                h = etree.HTML(self.browser.page_source)
                i = 6
            except Exception:
                i += 1
        if(self.count > 20):
            self.browser.quit()
            self.count = 0
            self.browser = webdriver.PhantomJS(service_args=service_args)
            self.browser.set_page_load_timeout(3)
        return {
            'src': h.xpath('//video/@src')
        }

if __name__ == '__main__':
    kw = '进'
    name = 'haizeiwang'
    comic = "https://m.manhuadui.com/manhua/haizeiwang/296660.html"
    sp = Spider()

    # search = sp.comic_search(kw, '1')
    # print('comicsearch', search)
    # item = sp.comic_item(name)
    # print('comicitem', item)
    # img = sp.comic_img(comic, '1')
    # print('comicimg', img)
    #
    # table = sp.animate_table()
    # print('animatetable', table)
    # search = sp.animate_search(kw)
    # print('animatesearch', search)
    # nameUrl = '/show/4642.html'
    # item = sp.animate_item(nameUrl)
    # print('animateitem', item)
    videoUrl = '/v/4642-4.html'
    video = sp.animate_video(videoUrl)
    print('animatevideo', video)
    # videoUrl = 'http://tup.yhdm.tv/?vid=http://quan.qq.com/video/1098_da55dca635b47b0826e85e5996f9d65c$mp4&m=1'
    # video = sp.video(videoUrl)
    # print('animatevideo', video)