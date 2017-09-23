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
from zhihusystem.items import ZhihuSystemItem

from PIL import Image

logger = logging.getLogger(__name__)

class ZhihuSipder(Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = [
        "https://www.zhihu.com/"
    ]
    start_user ='wang-tuan-jie-55'
    
    # 查询粉丝或者关注列表里面的用户需要附带的参数
    include_follow='data[*].answer_count, articles_count, gender, follower_count, is_followed, is_following, badge[?(type = best_answerer)].topics'
    # 查询个人信息需要附带的一个参数
    include_userinfo='locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,avatar_hue,answer_count,articles_count,pins_count,question_count,commercial_question_count,favorite_count,favorited_count,logs_count,marked_answers_count,marked_answers_text,message_thread_token,account_status,is_active,is_force_renamed,is_bind_sina,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics'
    # 获取粉丝列表的url, 里面的参数分别是用户的ID, 查询参数, offset表示第几页的粉丝或者关注者, limit表示每页的数量, 这里网页上默认是20    
    followers_url = 'https://www.zhihu.com/api/v4/members/{user_name}/followers?include={include_follow}&offset={offset}&limit={limit}'
    # 获取关注列表的URL, 里面的参数分别是用户的ID, 查询参数, offset表示第几页的粉丝或者关注者, limit表示每页的数量, 这里网页上默认是20
    followees_url = 'https://www.zhihu.com/api/v4/members/{user_name}/followees?include={include_follow}&offset={offset}&limit={limit}'
    # 提取用户信息信息的url
    userinfo_url= 'https://www.zhihu.com/api/v4/members/{user_name}?include={include_userinfo}'    
    
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
            "phone_num": 'user_name',
            "password": 'password',
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
        # 访问用户，获取详细信息
        yield scrapy.Request(url=self.userinfo_url.format(user_name=self.start_user,include_userinfo=self.include_userinfo),callback=self.get_user_info)
        # 用户的粉丝列表
        yield scrapy.Request(url=self.followers_url.format(user_name=self.start_user,include_follow=self.include_follow,offset=0,limit=20),callback=self.get_followers_parse)
        # 用户的关注列表
        yield scrapy.Request(url=self.followees_url.format(user_name=self.start_user,include_follow=self.include_follow,offset=0,limit=20),callback=self.get_followees_parse)
        
    # 获取用户信息信息
    def get_user_info(self,response):
        data = json.loads(response.text)
        item = ZhihuSystemItem()
        for Field in item.fields:
            if Field in data.keys():
                item[Field]=data.get(Field)
        yield item
        yield scrapy.Request(url=self.followers_url.format(user_name=data.get('url_token'),include_follow=self.include_follow,offset=0,limit=20),callback=self.get_followers_parse)
        yield scrapy.Request(url=self.followees_url.format(user_name=data.get('url_token'), include_follow=self.include_follow, offset=0,limit=20), callback=self.get_followees_parse)
        
    # 获取粉丝列表
    def get_followers_parse(self, response):
        try:#这里添加的异常是防止有些用户没有粉丝
            followers_data = json.loads(response.text)

            try:
                if  followers_data.get('data'):  # data里面是一个由字典组成的列表，每个字典是粉丝的相关信息
                    for one_user in followers_data.get('data'):
                        user_name = one_user['url_token']#提取url_token然后访问他的详细信息
                        yield scrapy.Request(url=self.userinfo_url.format(user_name=user_name,include_userinfo=self.include_userinfo),callback=self.get_user_info)
                        #将所有粉丝或者关注者的url_token提取出来，放进一开始我们构造的用户详细信息的网址里面，提取他们的信息

                if  'paging' in followers_data.keys() and followers_data.get('paging').get('is_end') ==False:
                    yield scrapy.Request(url=followers_data.get('paging').get('next'),callback=self.get_followers_parse)
            except Exception as e:
                print(e,'该用户没有url_token')
        except Exception as e:
            print(e,' 该用户没有粉丝')
            
    # 获取关注者的函数        
    def get_followees_parse(self,response):
        try:#这里添加的异常是防止有些用户没有关注者
            followees_data = json.loads(response.text)
            try:
                if followees_data.get('data'):
                    for one_user in followees_data.get('data'):
                        user_name = one_user['url_token']#提取url_token然后访问他的详细信息
                        yield scrapy.Request(url=self.userinfo_url.format(user_name=user_name,include_userinfo=self.include_userinfo),callback=self.get_user_info)
                        #将所有粉丝或者关注者的url_token提取出来，放进一开始我们构造的用户详细信息的网址里面，提取他们的信息

                if  'paging' in followees_data.keys() and followees_data.get('paging').get('is_end') ==False:#判断是否有下一页
                    yield scrapy.Request(url=followees_data.get('paging').get('next'),callback=self.get_followees_parse)
            except Exception as e:
                print(e,'该用户没有url_token或者data')
        except Exception as e:
            print(e,' 该用户没有粉丝')                            
        