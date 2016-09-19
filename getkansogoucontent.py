# -*- coding: utf-8 -*-

import sys
import time
import requests
from lxml import etree
from mysqlpooldao import MysqlDao
from redispooldao import RedisDao
from headers import Headers
from config import Config
import simplejson
import threading

reload(sys)
sys.setdefaultencoding('utf8')


class Worker(threading.Thread):
    def __init__(self, redisDao, mysqlDao):
        threading.Thread.__init__(self)
        self._redisDao = redisDao
        self._mysqlDao = mysqlDao

    def run(self):
        while True:
            print (self.getName())
            ret_json = self._redisDao.lpop('kansogou')
            if ret_json == None:
                break
            ret = simplejson.loads(ret_json)
            id = ret[0]
            category_id = ret[1]
            content_url = ret[2]
            img = ret[3]
            headers = Headers().getHeaders()
            print(content_url)
            try:
                req = requests.get(content_url, headers=headers, timeout=30)
                if req.status_code == 200:
                    html = req.content
                    selector = etree.HTML(html)
                    # 电影
                    if category_id == 1:
                        titles = selector.xpath('//*[@class="title txt-overflow"]/a[1]/text()')
                        play_urls = selector.xpath('//*[@class="title txt-overflow"]/a[1]/@href')
                        contents = selector.xpath('//*[@class="video-info"]/descendant::text()')
                    # 电视剧
                    if category_id == 2:
                        titles = selector.xpath('//*[@class="tt-mnc"]/text()')
                        play_urls = selector.xpath('//*[@class="tt-mnc"]/@href')
                        contents = selector.xpath('//*[@class="lines"]/descendant::text()')
                    # 综艺
                    if category_id == 3:
                        titles = selector.xpath('//*[@class="info"]/h1[1]/a[1]/text()')
                        play_urls = selector.xpath('//*[@class="info"]/h1[1]/a[1]/@href')
                        contents = selector.xpath('//*[@class="info"]/descendant::span/descendant::text()')
                    # 动漫
                    if category_id == 4:
                        titles = selector.xpath('//*[@class="title"]/a[1]/text()')
                        play_urls = selector.xpath('//*[@class="title"]/a[1]/@href')
                        contents = selector.xpath('//*[@class="video-info"]/descendant::text()')
                    title = play_url = content = ''
                    if len(titles) > 0:
                        title = titles[0]
                    if len(play_urls) > 0:
                        play_url = Config.url_main + play_urls[0]
                    content = simplejson.dumps(contents)
                    created_at = time.strftime('%Y-%m-%d %H:%M:%S')
                    # 存入content
                    sql = 'insert ignore into kansogou_content (`category_id`,`title`,`content`,`play_url`,`img`,`url`,`created_at`) VALUES (%s,%s,%s,%s,%s,%s,%s)'
                    values = (category_id, title, content, play_url, img, content_url, created_at)
                    print(title)
                    self._mysqlDao.executeValues(sql, values)
            except:
                self._mysqlDao = MysqlDao()
            # url置1
            sql = 'update kansogou_url set `status`=1 where `id`=' + str(id)
            self._mysqlDao.execute(sql)


if __name__ == '__main__':
    mysqlDao = MysqlDao()
    redisDao = RedisDao()
    while True:
        sql = 'select `id`,`category_id`,`url`,`img` from kansogou_url WHERE `status`=0 limit 0,100'
        ret = mysqlDao.execute(sql)
        # 如果取出来为空,程序结束
        if len(ret) == 0:
            break
        # 将mysql的数据存入redis队列
        for r in ret:
            r_json = simplejson.dumps(r)
            redisDao.rpush('kansogou', r_json)
        # 开始多线程
        worker_num = 1
        threads = []
        for x in xrange(0, worker_num):
            threads.append(Worker(redisDao, mysqlDao))
        for t in threads:
            t.setDaemon(True)
            t.start()
            # time.sleep(1)
        for t in threads:
            t.join()
        threads = []
    mysqlDao.close()
    print('game over')
