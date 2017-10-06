# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient
from scrapy.exceptions import DropItem

class MongoPipeline(object):
    collection_zhihuuser = 'users'
    collection_proxy = 'proxy'
    max_dropcount = 1000000  # 抓取数量
    current_dropcount = 0    # 当前数量

    def __init__(self, mongo_server, mongo_port, mongo_db, mongo_user, mongo_passwd):
        self.mongo_server = mongo_server
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.mongo_user = mongo_user
        self.mongo_passwd = mongo_passwd

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_server=crawler.settings.get('MONGODB_SERVER'),
            mongo_port=crawler.settings.get('MONGODB_PORT'),
            mongo_db=crawler.settings.get('MONGODB_DB'),
            mongo_user=crawler.settings.get('MONGO_USER'),
            mongo_passwd=crawler.settings.get('MONGO_PASSWD')
        )

    def open_spider(self, spider):
        uri = "mongodb://%s:%s@%s:%s" % (self.mongo_user, self.mongo_passwd, self.mongo_server, self.mongo_port)
        self.client = MongoClient(uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.current_dropcount += 1
        if(self.current_dropcount >= self.max_dropcount):
            spider.close_down = True
            raise DropItem("reach max limit")
        
        if "zhihuuser" == spider.name: 
            # 第一个参数传入查询条件，这里使用的是url_token，
            # 第二个参数传入字典类型的对象，就是我们的item，
            # 第三个参数传入True，这样就可以保证去重，如果查询数据存在的话就更新，不存在的话就插入。
            self.db[self.collection_zhihuuser].update({'url_token': item['url_token']}, {'$set': dict(item)}, True)
        return item
    
    
    