import time
import asyncio
import requests
import hashlib
import urllib.request
import urllib.error
import boto3
import os
import cfscrape

from functools import partial
from bs4 import BeautifulSoup
from copy import deepcopy
from datetime import datetime, timedelta

from db import session, engine

from models import Content

import models
import enums

from config import Config

s3 = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY_ID, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)
bucket = 'sichoi-scroll'

opener = urllib.request.build_opener()
opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8')]
urllib.request.install_opener(opener)

scraper = cfscrape.create_scraper()

class Crawler:
    """
    서비스 별 크롤러.
    """

    content_urls = None

    def __init__(self, base_url):
        self.base_url = base_url
        self.contents = []

    def req(self, params):
        return

    async def fetch(self, partial_method):
        print(partial_method)
        res = await loop.run_in_executor(None, partial_method)
        return BeautifulSoup(res.text, 'html.parser')


class Dogdrip(Crawler):
    # 마지막 페이지까지 탐색할 일반론적 방법 찾아야함

    def __init__(self):
        default_url = 'http://www.dogdrip.net/index.php'
        Crawler.__init__(self, default_url)

    async def __aenter__(self):
        pass

    async def __aexit__(self, *args):
        pass

    async def fetch_content_urls(self, params):
        bs = await Crawler.fetch(self, partial(scraper.get, url=self.base_url, params=params))
        arr = bs.select('.title > a')
        links = [c['href'].split('&')[-1] for c in arr]
        for l in links:
            if l not in self.contents:
                self.contents.append(l)

    async def fetch_contents(self, params):
        # bs = await Crawler.fetch(self, partial(scraper.get, url=self.base_url, params=params))
        bs = BeautifulSoup(requests.get(self.base_url, params).text, 'html.parser')

        res = self.parse_content(bs)
        if res is None:
            return
        print(res.title)
        # self.parse_comments(bs, params, res)

    def parse_content(self, bs):
        print('parse content')
        try:
            new = bs
            title = new.select('h4')[0].text
            m = hashlib.sha256(title.encode())
            hashed = m.hexdigest()

            date = None

            exist = session.query(Content).filter(Content.permanent_id == hashed).first()
            if exist:
                if date is None:
                    exist.created_at = datetime.utcnow() + timedelta(hours=9)
                else:
                    exist.created_at = date
                exist.origin = enums.DataOriginEnum.DOGDRIP
                session.commit()
                print('passed')
                return exist

            content = new.select('div#article_1')[0]
            length = len(content.select('img'))
            for img in content.select('img'):
                if 'sichoi-scroll' in img['src']:
                    print('continued')
                    continue
                if './' in img['src']:
                    img['src'] = img['src'].replace('./', 'http://www.dogdrip.net/')
                elif img['src'].startswith('/'):
                    img['src'] = 'https://www.dogdrip.net' + img['src']
                elif not img['src'].startswith('http'):
                    img['src'] = 'https://www.dogdrip.net/' + img['src']

                if 'transparent' in img['src']:
                    return
                
                for_img = hashlib.sha256(img['src'].encode())
                last = img['src'].split('.')[-1]
                rename = for_img.hexdigest()
                rename += '.' + last
                urllib.request.urlretrieve(img['src'], rename)
                s3.upload_file(rename, bucket, rename, ExtraArgs={'ACL': 'public-read'})
                os.remove(rename)
                img['src'] = 'http://d3q9984fv14hvr.cloudfront.net/' + rename
            content = content.decode()
        except Exception as e:
            print(e)
            print('what')
            return
        item = Content(title=title, data=content, permanent_id=hashed, created_at=date, origin=enums.DataOriginEnum.DOGDRIP)
        if item.created_at is None:
            item.created_at = datetime.utcnow() + timedelta(hours=9)
        session.add(item)
        session.commit()
        print('ad ded!')
        return item

    def parse_comments(self, bs, params, content):
        print('parse comments!')
        try:
            last_page = int(bs.select('div.replyBox > div.pagination.a1 > strong')[0].text)
        except:
            last_page = 1

        for i in range(last_page):
            page = i+1
            page_data_format = f'''<?xml version="1.0" encoding="utf-8" ?>
            <methodCall>
            <params>
            <document_srl><![CDATA[{params['document_srl']}]]></document_srl>
            <mid><![CDATA[dogdrip]]></mid>
            <cpage><![CDATA[{page}]]></cpage>
            <module><![CDATA[board]]></module>
            </params>
            </methodCall>'''
            res = scraper.post(url=self.base_url, headers={'Content-Type': 'text/plain'}, data=page_data_format) # TODO: 이부분 gather로 변경
            comment_page = BeautifulSoup(res.text, 'html.parser') # 이게 comments가 들어있는 html
            comments = comment_page.select('.replyItem')

            for comment in comments:
                created_at = datetime.strptime(' '.join(comment.select('.date')[0].text.replace('\n', '').replace('\t', '').split(' ')[:2]), '%Y.%m.%d %H:%M:%S') # TODO: date 정확히 구해와야함
                text = comment.select('.comment')[0].text
                permanent_id = comment.select('a[name]')[0]['name'].split('_')[1]

                comment_obj = session.query(models.Comment).\
                        filter(models.Comment.permanent_id == permanent_id).\
                        first()

                if comment_obj is not None:
                    print('comment already proceed')
                    continue

                parent_id = None
                if 'parent_srl' in comment.attrs:
                    parent_comment = session.query(models.Comment).\
                            filter(models.Comment.permanent_id == int(comment['parent_srl'])).\
                            first()
                    parent_id = parent_comment.id
                comment_obj = models.Comment(data=text, created_at=created_at, permanent_id=permanent_id, parent_id=parent_id)
                comment_obj.cid = content.id
                session.add(comment_obj)
                session.flush()
                # TODO: comment to comment의 relationship 정리 후 DB에create
                # 댓글 정렬 방법
                # 1. parent_comment가 없는 애들을 다 가져온다
                # 2. 다 가져와서 created_at 으로 정렬
                # 3. comment들의 child조사
                # 4. child를 created_at 순서대로 끼워넣어준다
                # 5. child를 대상으로 3->4 반복.
                # parent = 
                print(text)
        session.commit()

    async def run(self):
        a = time.time()

        fts = []
        for x in range(263):
            fts.append(asyncio.ensure_future(self.fetch_content_urls({'mid': 'dogdrip', 'page': x, 'sort_index': 'popular'})))

        await asyncio.gather(*fts)
        b = time.time()
        print(b - a)
        print(len(self.contents))

        fts = []
        for c in self.contents:
            k, v = c.split('=')
            fts.append(asyncio.ensure_future(self.fetch_contents({k: v})))

        await asyncio.gather(*fts)


async def crawl():
    dogdrip = Dogdrip()
    async with dogdrip:
        await dogdrip.run()
        session.commit()
    print('ended')


loop = asyncio.get_event_loop()
loop.run_until_complete(crawl())
# loop.close()
