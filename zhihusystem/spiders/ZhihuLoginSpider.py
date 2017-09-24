# -*- coding: utf-8 -*-
'''
Created on 2017年9月23日

@author: Administrator
'''
import logging
import os
import json
import time
import scrapy
from scrapy.spiders import Spider

from PIL import Image

logger = logging.getLogger(__name__)

class ZhihuLoginSipder(Spider):
    name = 'zhihuLogin'
    allowed_domains = ['www.zhihu.com']
    start_urls = [
        "https://www.zhihu.com/people/zhoumaoen"
    ]
    
    def start_requests(self):
        captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + str(int(time.time() * 1000)) + '&type=login&lang=en'
        return [scrapy.Request(url=captcha_url, callback=self.parser_captcha)]
    
    def parser_captcha(self, response):
        with open('captcha.jpg', 'wb') as f:
            f.write(response.body)
            f.close()
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
        captcha = input("please input the captcha\n>")
        return [scrapy.FormRequest(url='https://www.zhihu.com/#signin', callback=self.login, meta={'captcha': captcha})]

    def login(self, response):
        xsrf = response.xpath("//input[@name='_xsrf']/@value").extract_first()
        if xsrf is None:
            return ''
        post_url = 'https://www.zhihu.com/login/phone_num'
        post_data = {
            "_xsrf": xsrf,
            "phone_num": self.crawler.settings.get("PHONE_NUM"),
            "password": self.crawler.settings.get("PASSWORD"),
            "captcha": response.meta['captcha']
        }
        return [scrapy.FormRequest(url=post_url, formdata=post_data, callback=self.check_login)]

    # 验证返回是否成功
    def check_login(self, response):
        js = json.loads(response.text)
        if 'msg' in js and js['msg'] == u'登录成功':
            for url in self.start_urls:
                yield self.make_requests_from_url(url)
        else:
            print u'登录失败', js
            
    def parse(self, response):
        print response.url
        if "周茂恩" in response.body:
            print u'登录成功'