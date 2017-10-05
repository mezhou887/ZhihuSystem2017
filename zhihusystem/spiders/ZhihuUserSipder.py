# -*- coding: utf-8 -*-
'''
Created on 2017年9月23日

@author: Administrator
'''
import logging
import json
import scrapy
from scrapy.spiders import Spider
from scrapy.exceptions import CloseSpider
from zhihusystem.items import ZhihuUserItem

logger = logging.getLogger(__name__)

class ZhihuUserSipder(Spider):
    name = 'zhihuuser'
    allowed_domains = ['www.zhihu.com']
    start_urls = [
        "https://www.zhihu.com/"
    ]
    start_user ='zhoumaoen'
    close_down = False
    
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
    
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Connection": "keep-alive",
        "Content-Type":" application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0",
        "Referer": "http://www.zhihu.com/",
        "X-Requested-With": "XMLHttpRequest",
        "authorization": "oauth c3cef7c66a1843f8b3a9e6a1e3160e20",
    } 
   
    
    def parse(self, response):
        # 访问用户，获取详细信息
        yield scrapy.Request(url=self.userinfo_url.format(user_name=self.start_user,include_userinfo=self.include_userinfo)
                             ,headers=self.headers,callback=self.parse_user)
        # 用户的粉丝列表
        yield scrapy.Request(url=self.followers_url.format(user_name=self.start_user,include_follow=self.include_follow,offset=0,limit=20)
                             ,headers=self.headers,callback=self.paese_followers)
        # 用户的关注列表
        yield scrapy.Request(url=self.followees_url.format(user_name=self.start_user,include_follow=self.include_follow,offset=0,limit=20)
                             ,headers=self.headers,callback=self.paese_follows)


    def check_closed(self):
        if(self.close_down == True):
            raise CloseSpider(reason = "reach max limit")    

        
    # 详细信息的提取和粉丝关注列表的获取
    def parse_user(self,response):
        self.check_closed()
        data = json.loads(response.text)
        item = ZhihuUserItem()
        for Field in item.fields:
            if Field in data.keys():
                item[Field]=data.get(Field)
        yield item
        yield scrapy.Request(url=self.followers_url.format(user_name=data.get('url_token'),include_follow=self.include_follow,offset=0,limit=20)
                             ,headers=self.headers,callback=self.paese_followers)
        yield scrapy.Request(url=self.followees_url.format(user_name=data.get('url_token'), include_follow=self.include_follow, offset=0,limit=20)
                             ,headers=self.headers,callback=self.paese_follows)
        
        
    # 实现了通过粉丝列表重新请求用户并进行翻页的功能
    def paese_followers(self, response):
        self.check_closed()
        #添加异常是防止有些用户没有粉丝
        try:
            followers_data = json.loads(response.text)

            try:
                # data里面是一个由字典组成的列表，每个字典是粉丝的相关信息
                if  followers_data.get('data'):  
                    for one_user in followers_data.get('data'):
                        # 提取url_token然后访问他的详细信息
                        user_name = one_user['url_token']
                        # 将所有粉丝的url_token提取出来，放进一开始我们构造的用户详细信息的网址里面，提取他们的信息
                        yield scrapy.Request(url=self.userinfo_url.format(user_name=user_name,include_userinfo=self.include_userinfo)
                                             ,headers=self.headers,callback=self.parse_user)
                        

                if  'paging' in followers_data.keys() and followers_data.get('paging').get('is_end')==False:
                    yield scrapy.Request(url=followers_data.get('paging').get('next'),headers=self.headers,callback=self.paese_followers)
            except Exception as e:
                print(e,'该用户没有url_token')
        except Exception as e:
            print(e,'该用户没有粉丝')
     
            
    # 实现了通过关注列表重新请求用户并进行翻页的功能
    def paese_follows(self,response):
        self.check_closed()
        #添加异常是防止有些用户没有关注者
        try:
            followees_data = json.loads(response.text)
            try:
                if followees_data.get('data'):
                    for one_user in followees_data.get('data'):
                        # 提取url_token然后访问他的详细信息
                        user_name = one_user['url_token']
                        # 将所有关注者的url_token提取出来，放进一开始我们构造的用户详细信息的网址里面，提取他们的信息
                        yield scrapy.Request(url=self.userinfo_url.format(user_name=user_name,include_userinfo=self.include_userinfo)
                                             ,headers=self.headers,callback=self.parse_user)
                        

                if  'paging' in followees_data.keys() and followees_data.get('paging').get('is_end')==False:#判断是否有下一页
                    yield scrapy.Request(url=followees_data.get('paging').get('next'),headers=self.headers,callback=self.paese_follows)
            except Exception as e:
                print(e,'该用户没有url_token或者data')
        except Exception as e:
            print(e,'该用户没有粉丝')                            
        