# -*- coding: utf-8 -*-

import sys
import time
import traceback
import requests
from lxml import etree
from mysqlpooldao import MysqlDao
from headers import Headers
from config import Config


def getEndPage(category_url):
    end_page = 10
    headers = Headers().getHeaders()
    try:
        req = requests.get(category_url, headers=headers, timeout=30)
        if req.status_code == 200:
            html = req.content
            selector = etree.HTML(html)
            end_pages = selector.xpath('//div[@class="sub-pager-bar"]/a[last()-1]/@href')
            if len(end_pages):
                end_page = end_pages[0].split('-')[-1].replace('/', '')
    except:
        traceback.print_exc()
    return int(end_page)


def getContentUrls(url, category_id, mysqlDao):
    print('urlstart:' + url)
    headers = Headers().getHeaders()
    try:
        req = requests.get(url, headers=headers, timeout=30)
        if req.status_code == 200:
            html = req.content
            selector = etree.HTML(html)
            if category_id == 1 or category_id == 2:
                content_urls = selector.xpath('//div[@class="cell cf"]/a[1]/@href')
                content_imgs = selector.xpath('//div[@class="cell cf"]/a[1]/img/@src')
            else:
                content_urls = selector.xpath('//div[@class="cell"]/a[1]/@href')
                content_imgs = selector.xpath('//div[@class="cell"]/a[1]/img/@src')
            content_urls.reverse()
            print(content_imgs)
            content_imgs.reverse()
            n = 0
            for content_url in content_urls:
                try:
                    content_img = content_imgs[n]
                except:
                    content_img = ''
                n = n + 1
                content_url = Config.url_main + content_url
                created_at = time.strftime('%Y-%m-%d %H:%M:%S')
                sql = 'insert ignore into kansogou_url (`category_id`,`url`,`img`,`status`,`created_at`) VALUES (%s,%s,%s,%s,%s)'
                values = (category_id, content_url, content_img, 0, created_at)
                print(content_url)
                mysqlDao.executeValues(sql, values)

    except Exception, e:
        print(Exception, e)
        traceback.print_exc()


mysqlDao = MysqlDao()
sql = 'select * from kansogou_category'
categorys = mysqlDao.execute(sql)
is_from_end_page = False
for category in categorys:
    category_id = category[0]
    category_url = category[2]
    if is_from_end_page:
        end_page = getEndPage(category_url)
    else:
        end_page = 10
    while True:
        if end_page == 0:
            break
        url = category_url + str(end_page)
        getContentUrls(url, category_id, mysqlDao)
        end_page = end_page - 1
mysqlDao.close()
