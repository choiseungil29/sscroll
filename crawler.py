import time
import asyncio
import requests
import hashlib
import urllib.request
import urllib.error
import urllib.parse as urlparse
import boto3
import os
import cfscrape
import traceback

from functools import partial
from bs4 import BeautifulSoup
from copy import deepcopy
from datetime import datetime, timedelta

from db import session, engine

from app import models

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
        return BeautifulSoup(res.text.encode(), 'html.parser')


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
        res = self.parse_comments(bs, res, params)
        print(res.title)

    def parse_content(self, bs):
        print('parse content')
        try:
            new = bs
            title = new.select('h4')[0].text
            m = hashlib.blake2b(digest_size=12)
            m.update(title.encode())
            hashed = m.hexdigest()

            date = None

            exist = session.query(models.Content).filter(models.Content.permanent_id == hashed).first()
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
                s3.upload_file(rename, bucket, rename, ExtraArgs={'ACL': 'public-read', 'CacheControl': 'max-age=86400'})
                os.remove(rename)
                img['src'] = 'http://d3q9984fv14hvr.cloudfront.net/' + rename
            content = content.decode()
        except Exception as e:
            print('exit')
            traceback.print_tb(e.__traceback__)
            return
        item = models.Content(title=title, data=content, permanent_id=hashed, created_at=date, origin=enums.DataOriginEnum.DOGDRIP)
        if item.created_at is None:
            item.created_at = datetime.utcnow() + timedelta(hours=9)
        session.add(item)
        session.commit()
        print('added!')
        return item

    def parse_comments(self, bs, content, params):
        comments = session.query(models.Comment).\
                filter(models.Comment.cid == content.id).\
                all()

        if len(comments) > 0:
            print('alread updated')
            return
        
        comment_top = bs.find('div', id='comment_top')
        last_page = self.get_comment_last_page(comment_top)
        for i in range(last_page + 1):
            param = params
            params['cpage'] = i
            res = BeautifulSoup(requests.get(self.base_url, params).text, 'html.parser')
            comment_list = res.find('div', id='commentbox').find('div', attrs={'class': 'comment-list'})
            for comment_box in comment_list.findAll(lambda x: x.name == 'div' and 'class' in x.attrs and 'depth' not in x.attrs['class'] and 'comment-item' in x.attrs['class']):
                box = comment_box.select('> div')[0].select('> div')[0]

                text = box.find('div', attrs={'class': 'xe_content'}).text
                created_at = datetime.utcnow() + timedelta(hours=9)
                try:
                    created_at = datetime.strptime(box.find('div').findAll('div')[-1].find('span').text, '%Y.%m.%d')
                except Exception as e:
                    pass
                comment = models.Comment(data=text, cid=content.id, created_at=created_at)
                session.add(comment)
                session.flush()
                print(text)

        session.commit()

    def get_comment_last_page(self, bs):
        try:
            comment_pages = bs.findAll(lambda x: x.name == 'a' and 'href' in x.attrs and '#comment' in x.attrs['href'])
            parsed = urlparse.urlparse(comment_pages[-1]['href'])
            qs = urlparse.parse_qs(parsed.query)
        except Exception as e:
            return 1
        return int(qs['cpage'][0]) + 1

    async def run(self):
        a = time.time()

        fts = []
        for x in range(263):
            fts.append(asyncio.ensure_future(self.fetch_content_urls({'mid': 'dogdrip', 'page': x, 'sort_index': 'popular', 'cpage': 1})))

        await asyncio.gather(*fts)
        b = time.time()
        print(b - a)
        print(len(self.contents))

        fts = []
        for c in self.contents:
            k, v = c.split('=')
            fts.append(asyncio.ensure_future(self.fetch_contents({k: v})))
            # fts.append(asyncio.ensure_future(self.fetch_contents({k: '115890448'})))

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
