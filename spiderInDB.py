#此代码将漫画堆的所有漫画信息存入mysql数据库
#也可用于爬完之后的持续更新
#此代码采用了多线程爬取，参照的是：https://blog.csdn.net/gyt15663668337/article/details/86345690

#设定数据库参数,数据表结构在comic_info.sql
host = "localhost"
user = "root"
password = ""
db = "coldrain"
port = 3306

import threading
import time
import queue
import pymysql
from spider import Spider

#预置爬取的漫画总数为 258*20
total = 258
sql_insert = """insert into comic_info values ('%d',"%s","%s","%s","%s","%s","%s", NULL, NULL, NULL, NULL, NULL, NULL)"""
sql_select = """select cslug from comic_info where cid = '%d' and clastname != "%s" """
sql_update = """update comic_info set clastname = "%s", cserialise = '%d' where cid = '%d'"""
sql_update2 = """update comic_info set ctype = "%s", ccategory = "%s", carea = "%s", cupdate = "%s", cchapters = "%s", cchapterurl = "%s" where cslug = '%s'"""
threadList = ["Thread-1", "Thread-2", "Thread-3", "Thread-4"]

sp = Spider()
#尝试获取总页数
try:
    total = sp.comic_search('', '1')['_meta']['pageCount'] + 1
except:
    print('查找总页数出错')

workQueue = queue.Queue(total * 21)
# 用页码填充队列
for page in range(1, total):
    workQueue.put(page)
spiderUrls = []
threading.TIMEOUT_MAX = 10
#设置线程
class myThread(threading.Thread):
    def __init__(self, name, q, flag):
        threading.Thread.__init__(self)
        self.name = name
        self.q = q
        self.flag = flag
        #数据库连接
        self.db = pymysql.connect(host=host, user=user,
                             password=password, db=db, port=port, charset='utf8')
        self.cur = self.db.cursor()
    def run(self):
        print("Starting " + self.name)
        if (self.flag == 1):
            while True:
                try:    updateComicList(self.name, self.q, self.db, self.cur)
                except: break
        elif (self.flag == 2):
            while True:
                try:    updateComic(self.name, self.q, self.db, self.cur)
                except: break
        self.cur.close()
        self.db.close()
        print("Exiting ",self.name)

#先爬"https://450.manhuadang.net/comic/search"获取漫画列表和需要更新的漫画
def updateComicList(threadName, q, db, cur):
    #将页码弹出队列
    page = q.get(timeout=2)
    url = "https://450.manhuadang.net/comic/search?page=" + str(page)
    try:
        items = sp.comic_search('', str(page))['items']
        for item in items:
            try:
                #由于封面url部分格式特殊，无法访问，需先处理下，如"https://res.333dm.com/http://mh.manhuazj.com/Uploads/vod/2019-04-02/5ca33ad82f91c.jpg"
                coverUrl = item['coverUrl'][item['coverUrl'].rindex('http'):]
                #执行插入语句
                cur.execute(sql_insert % (item['id'], item['name'], item['slug'], coverUrl
                                          , item['last_chapter_name'], item['author'], item['serialise']))  # 执行sql语句
                db.commit()
                #将item['slug']存入数组供后续的详情页爬取
                spiderUrls.append(item['slug'])

            except Exception as ex:
                db.rollback()
            try:
                #执行select语句查看数据库中该漫画最新章节和刚爬到的是否一致
                cur.execute(sql_select % (item['id'], item['last_chapter_name']))  # 执行sql语句
                results = cur.fetchall()
                for row in results:
                    #如果不一致，则更新该漫画的最新章节，并存入数组供后续爬取
                   print('有更新')
                   spiderUrls.append(row[0])
                   try:
                       cur.execute(sql_update % (item['last_chapter_name'], item['serialise'], item['id']))  # 执行sql语句
                       db.commit()
                   except Exception as exc:
                       db.rollback()
                       print(exc)

            except Exception as ex:
                print(ex)
        print(q.qsize(), threadName, url, len(spiderUrls))
    except Exception as e:
        print(q.qsize(), threadName, url, 'Error', e)
        q.put(page)

#爬取漫画详细页
def updateComic(threadName, q, db, cur):
    #弹出漫画名对应的字符串
    name = q.get(timeout=2)
    try:
        res = sp.comic_item(name)
        #爬到的type(类型)、chapterName(章节名)、chapterUrl(章节url)都是数组，将它们用|合并
        type = ''
        for ty in res['type']:
            type += ty + '|'
        type = type[:-1]
        chapterName = ''
        for chapter in res['chapterName']:
            chapterName += chapter + '|'
        chapterName = chapterName[:-1]
        chapterUrl = ''
        for chapter in res['chapterURL']:
            chapterUrl += chapter + '|'
        chapterUrl = chapterUrl[:-1]
        try:    category = res['category'][0]
        except: category = ''
        try:    update = res['update'][0]
        except: update = ''
        try:    area = res['area'][0]
        except: area = ''
        try:
            #执行更新语句
            cur.execute(sql_update2 % (type, category, area, update, chapterName, chapterUrl, name))  # 执行sql语句
            db.commit()
        except Exception as exc:
            db.rollback()
            print(exc)
        print(q.qsize(), threadName, name)
    except Exception as e:
        q.put(name)
        print(q.qsize(), threadName, name, 'Error', e)

start = time.time()
# 创建新线程
threads = []
for tName in threadList:
    thread = myThread(tName, workQueue, 1)
    thread.start()
    threads.append(thread)

# 等待所有线程完成
for t in threads:
    t.join()
end = time.time()
print("爬取列表总时间为：", end-start)


time.sleep(2)

start = time.time()
for name in spiderUrls:
    workQueue.put(name)

threads = []
for tName in threadList:
    thread = myThread(tName, workQueue, 2)
    thread.start()
    threads.append(thread)

for t in threads:
    t.join()
end = time.time()
print("爬取详细信息总时间为：", end-start)