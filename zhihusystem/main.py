# -*- coding: utf-8 -*-
'''
Created on 2017年9月10日

@author: Administrator
'''

import os

from scrapy import cmdline
if __name__ =="__main__":
    
    for fpathe,dirs,fs in os.walk(os.path.abspath('.')):
        for f in fs:
            if f.endswith('.pyc') or f.endswith('.csv')or f.endswith('.json'):
                os.remove(os.path.join(fpathe,f));    
    
#     cmdline.execute("scrapy crawl zhihuLogin -o zhihuLogin.csv".split())
    cmdline.execute("scrapy crawl zhihuuser -o zhihuuser.csv".split())
    
    