# 此代码创建了爬虫的api

from flask import Flask,request
import flask_restful
from flask_restful import Resource
from spider import Spider

app = Flask("Spider")
api = flask_restful.Api(app)
sp = Spider()
#搜索页面api
class ComicSearch(Resource):
        def get(self):
            kw = request.args.get('kw')
            p = request.args.get('p')
            return sp.comic_search(kw, p)
#详情页面api
class ComicItem(Resource):
    def get(self):
        name = request.args.get('slug')
        return sp.comic_item(name)
#章节页面api
class ComicImg(Resource):
    def get(self):
        url = request.args.get('ch')
        p = request.args.get('p')
        #重试6次
        i = 0
        while i < 6:
            try:
                return sp.comic_img(url, p)
                i = 6
            except:
                i += 1

api.add_resource(ComicSearch, '/spider/comicsearch')
api.add_resource(ComicItem, '/spider/comicitem')
api.add_resource(ComicImg, '/spider/comicimg')

if __name__ == '__main__':
    #主机为本地，端口号为5000
    #api举例：localhost:5000/spider/comicsearch?kw=进&p=1
    app.run(host='localhost', port=5000, debug=True)
