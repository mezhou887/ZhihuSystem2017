# -*- coding: utf-8 -*-
'''
Created on 2017年9月24日

@author: Administrator
'''
import logging
from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor as sle
from scrapy.selector import Selector
from zhihusystem.items import XiCiDaiLiItem
from scrapy.http import Request

logger = logging.getLogger(__name__)

class XiCiDaiLiSpider(CrawlSpider):
    name = 'xicidaili'
    allowed_domains = ['www.xicidaili.com']
    start_urls = [
        'http://www.xicidaili.com/nn',
        'http://www.xicidaili.com/nt',
        'http://www.xicidaili.com/wn'
    ]
     
    rules = [
        Rule(sle(allow=("/nn/[\d]{1,2}$")), callback='parse_proxy', follow=True),
        Rule(sle(allow=("/nt/[\d]{1,2}$")), callback='parse_proxy', follow=True),
        Rule(sle(allow=("/wn/[\d]{1,2}$")), callback='parse_proxy', follow=True),
    ]
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, sdch",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0",
    } 
    
    def start_requests(self): 
        for url in self.start_urls:
            yield Request(url, headers=self.headers, dont_filter=True)
                
    def parse_proxy(self, response):
        logger.debug('parse_proxy: '+response.url);
        table = Selector(response).xpath('//table[@id="ip_list"]')[0]
        trs = table.xpath('//tr')[1:]   #去掉标题行        
        
        items = [];
        for tr in trs: 
            item = XiCiDaiLiItem();
            item['ip'] = tr.xpath('td[2]/text()').extract()[0]
            item['port'] = tr.xpath('td[3]/text()').extract()[0]
            item['position'] = tr.xpath('string(td[4])').extract()[0].strip()
            item['type'] = tr.xpath('td[6]/text()').extract()[0]
            item['speed'] = tr.xpath('td[7]/div/@title').re('\d+\.\d*')[0]
            item['last_check_time'] = tr.xpath('td[10]/text()').extract()[0]
            
            if 'http' in item['type']: 
                logger.info('function: parse_proxy, url: '+response.url+' , item: '+str(item));
                items.append(item)
            
        return items;