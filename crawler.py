import time
import asyncio
import requests
import hashlib
import urllib.request
import urllib.error
import urllib.parse as urlparse
import boto3
import os
import re
import cfscrape
import traceback
import sys

from functools import partial
from bs4 import BeautifulSoup
from copy import deepcopy
from datetime import datetime, timedelta

from db import session, engine

from app import models

import enums

from config import Config

s3 = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY_ID, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)
bucket = 'img.sscroll.net'

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
        bs = await Crawler.fetch(self, partial(scraper.get, url=self.base_url, params=params))
        # bs = BeautifulSoup(requests.get(self.base_url, params).text, 'html.parser')

        res = self.parse_content(bs)
        if res is None:
            return
        res = self.parse_comments(bs, res, params)
        print(res.title)

    def parse_content(self, bs):
        print('parse content')
        try:
            new = bs
            print(bs)
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
            
            date = None
            for date_obj in new.select('div.ed.flex.flex-wrap.flex-left.flex-middle.title-toolbar span.ed.text-xsmall.text-muted'):
                text = date_obj.text
                delta = None
                if '일 전' in text:
                    delta = timedelta(days=int(text[0]))
                if '시간 전' in text:
                    delta = timedelta(hours=int(text[0]))
                if '분 전' in text:
                    delta = timedelta(minutes=int(text[0]))
                    
                if delta is not None:
                    date = datetime.utcnow() + timedelta(hours=9) - delta
                else:
                    try:
                        date = datetime.strptime(text, '%Y.%m.%d')
                    except:
                        print('continued')
                        continue
                    break
                    

            '''delta = None
            if '일 전' in date:
                delta = timedelta(days=int(date[0]))
            if '시간 전' in date:
                delta = timedelta(hours=int(date[0]))
            if '분 전' in date:
                delta = timedelta(minutes=int(date[0]))
            
            if delta is not None:
                date = datetime.utcnow() + timedelta(hours=9) - delta
            else:
                breakpoint()
                date = datetime.strptime(date, '%Y.%m.%d')'''
            
            # writer = new.select('div.ed.flex.flex-wrap.flex-left.flex-middle.title-toolbar > div.ed.flex.flex-wrap a')
            writer = new.select('div.title-toolbar span')[0].text.strip()
            writer = hashlib.shake_128(writer.encode()).hexdigest(length=4)

            user = models.User(nickname=writer)
            session.add(user)
            session.flush()

            # TODO 2: 작성자 아이디 구해와서 해싱
            # DOIT!

            content = new.select('div.ed.article-wrapper.inner-container > div.ed > div')[1]
            content = content.select('div')[0]
            # breakpoint()
            # content = new.select('div#article_1')[0]
            for img in content.select('img'):
                if 'img.sscroll.net' in img['src']:
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
                s3.upload_file(rename, bucket, 'upload/' + rename, ExtraArgs={'ACL': 'public-read', 'CacheControl': 'max-age=2592000'})
                os.remove(rename)
                img['src'] = 'http://img.sscroll.net/upload/'+ rename
            
            for video in content.select('source'):
                if 'img.sscroll.net' in video['src']:
                    print('continued')
                    continue
                if './' in video['src']:
                    video['src'] = video['src'].replace('./', 'http://www.dogdrip.net/')
                elif video['src'].startswith('/'):
                    video['src'] = 'https://www.dogdrip.net' + video['src']
                elif not video['src'].startswith('http'):
                    video['src'] = 'https://www.dogdrip.net/' + video['src']

                if 'transparent' in video['src']:
                    return

                for_img = hashlib.sha256(video['src'].encode())
                last = video['src'].split('.')[-1]
                rename = for_img.hexdigest()
                rename += '.' + last
                urllib.request.urlretrieve(video['src'], rename)
                s3.upload_file(rename, bucket, 'upload/' + rename, ExtraArgs={'ACL': 'public-read', 'CacheControl': 'max-age=2592000'})
                os.remove(rename)
                video['src'] = 'http://img.sscroll.net/upload/'+ rename

            content = content.decode()
        except Exception as e:
            print('exit')
            traceback.print_tb(e.__traceback__)
            return
        item = models.Content(title=title, data=content, permanent_id=hashed, created_at=date, origin=enums.DataOriginEnum.DOGDRIP, uid=user.id)
        if item.created_at is None:
            item.created_at = datetime.utcnow() + timedelta(hours=9)
        
        data = new.select('script[type="text/javascript"]')[0].text
        try:
            up, down = filter(lambda x: x != '', re.compile('[0-9]*').findall(data))
            item.up = up
            item.down = down
        except:
            pass
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
        before_comment = None
        for i in range(last_page + 1):
            param = params
            params['cpage'] = i
            res = BeautifulSoup(requests.get(self.base_url, params).text, 'html.parser')
            comment_list = res.find('div', id='commentbox').find('div', attrs={'class': 'comment-list'})
            # for comment_box in comment_list.findAll(lambda x: x.name == 'div' and 'class' in x.attrs and 'depth' not in x.attrs['class'] and 'comment-item' in x.attrs['class']):
            for comment_box in comment_list.findAll(lambda x: x.name == 'div' and 'class' in x.attrs and 'comment-item' in x.attrs['class']):
                box = comment_box.select('> div')[0].select('> div')[0]

                try:
                    text = box.find('div', attrs={'class': 'xe_content'}).text
                except Exception as e:
                    continue
                if not text:
                    before_comment = None
                    print('continued')
                    break
                date = box.find('div').findAll('div')[-1].find('span').text
                delta = None
                if '일 전' in date:
                    delta = timedelta(days=int(date[0]))
                if '시간 전' in date:
                    delta = timedelta(hours=int(date[0]))
                if '분 전' in date:
                    delta = timedelta(minutes=int(date[0]))

                if delta is not None:
                    date = datetime.utcnow() + timedelta(hours=9) - delta
                else:
                    date = datetime.strptime(date, '%Y.%m.%d')
                
                selected = box.select('div.comment-bar > div')
                if len(selected) == 0:
                    selected = box.select('div.comment-bar-author > div')
                writer = selected[0].text.strip()
                # writer = box.select('a.ed.link-reset')[0].text
                writer = hashlib.shake_128(writer.encode()).hexdigest(length=4)

                user = session.query(models.User).\
                    filter(models.User.nickname == writer).\
                    first()
                
                if user is None:
                    user = models.User(nickname=writer)
                    session.add(user)
                    session.flush()
                
                comment = models.Comment(data=text, cid=content.id, created_at=date, uid=user.id)
                if 'depth' in comment_box.attrs['class'] and before_comment:
                    target = box.select('span.ed.label-primary')[0].text.strip()[1:]
                    target = hashlib.shake_128(target.encode()).hexdigest(length=4)
                    comment.data = f'@{target} {comment.data}'
                    comment.parent_id = before_comment.id
                else:
                    before_comment = comment
                
                exist = session.query(models.Comment).\
                    filter(models.Comment.uid == user.id).\
                    first()
                if not exist:
                    session.add(comment)
                    session.flush()
                    print(text)

        session.commit()
        return content

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
            print(c)
            k, v = c.split('=')
            fts.append(asyncio.ensure_future(self.fetch_contents({k: v})))

        await asyncio.gather(*fts)


async def crawl():
    dogdrip = Dogdrip()
    async with dogdrip:
        await dogdrip.run()
        session.commit()
    print('ended')

async def crawl_target(url):
    dogdrip = Dogdrip()
    async with dogdrip:
        params = {}
        if len(url.split('?')) == 1:
            params['document_srl'] = url.split('/')[-1]
        else:
            for param in url.split('?')[1].split('&'):
                k, v = param.split('=')
                params[k] = v
        await dogdrip.fetch_contents(params)


loop = asyncio.get_event_loop()
if len(sys.argv) > 1:
    loop.run_until_complete(crawl_target(sys.argv[1]))
        
else:
    loop.run_until_complete(crawl())
# loop.close()


