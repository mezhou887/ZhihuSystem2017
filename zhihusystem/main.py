# -*- coding: utf-8 -*-
'''
Created on 2017年9月10日

@author: Administrator
'''

import os

from scrapy import cmdline
#   －o 代表输出文件 －t 代表文件格式
if __name__ =="__main__":
    
    for fpathe,dirs,fs in os.walk(os.path.abspath('.')):
        for f in fs:
            if f.endswith('.pyc') or f.endswith('.json'):
                os.remove(os.path.join(fpathe,f));    
    
#     cmdline.execute("scrapy crawl zhihuLogin -o zhihuLogin.csv".split())
    cmdline.execute("scrapy crawl zhihuuser".split())
#     cmdline.execute("scrapy crawl xicidaili".split())
    
    